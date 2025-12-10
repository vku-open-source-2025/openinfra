"""Rain Forecast Service for detecting abnormal rain accumulation using ARIMA time series forecasting."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from motor.motor_asyncio import AsyncIOMotorDatabase

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.stattools import adfuller

    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    logging.warning(
        "statsmodels not available. Rain forecast service will use fallback methods."
    )

logger = logging.getLogger(__name__)

# Configuration constants
ANOMALY_THRESHOLD_MULTIPLIER = 2.0
MIN_DATA_POINTS = 48  # Minimum hourly readings needed for training (2 days)
FORECAST_HORIZON = 1  # Hours ahead to forecast
TRAINING_WINDOW_DAYS = 7


class RainForecastService:
    """Service for forecasting rain accumulation and detecting anomalies."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize the rain forecast service."""
        self.db = db
        if not STATSMODELS_AVAILABLE:
            logger.warning(
                "statsmodels not available. Using simplified threshold-based detection."
            )

    async def get_historical_baseline(
        self, sensor_id: str, days: int = TRAINING_WINDOW_DAYS
    ) -> List[Dict]:
        """
        Fetch historical rainfall data from MongoDB.

        Args:
            sensor_id: Sensor ID to fetch data for
            days: Number of days of historical data to fetch

        Returns:
            List of reading dictionaries with timestamp and value
        """
        from_time = datetime.utcnow() - timedelta(days=days)
        to_time = datetime.utcnow()

        cursor = (
            self.db["sensor_readings"]
            .find(
                {
                    "sensor_id": sensor_id,
                    "timestamp": {"$gte": from_time, "$lte": to_time},
                }
            )
            .sort("timestamp", 1)
        )

        readings = []
        async for reading in cursor:
            readings.append(
                {
                    "timestamp": reading.get("timestamp"),
                    "value": reading.get("value", 0),
                    "unit": reading.get("unit", "mm"),
                }
            )

        return readings

    def resample_rainfall_data(
        self, readings: List[Dict], interval: str = "1H"
    ) -> pd.Series:
        """
        Resample irregular sensor readings to regular hourly intervals.

        Args:
            readings: List of reading dictionaries with timestamp and value
            interval: Pandas frequency string (default: '1H' for hourly)

        Returns:
            Pandas Series with datetime index and rainfall values
        """
        if not readings:
            return pd.Series(dtype=float)

        # Convert to DataFrame
        df = pd.DataFrame(readings)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)

        # Resample to hourly intervals, summing rainfall values
        # Forward fill missing values within the same hour
        resampled = df["value"].resample(interval).sum()

        return resampled

    def calculate_accumulation(
        self, readings: List[Dict], window_hours: int = 1
    ) -> float:
        """
        Calculate cumulative rainfall over a time window.

        Args:
            readings: List of reading dictionaries
            window_hours: Time window in hours

        Returns:
            Total rainfall accumulation in mm
        """
        if not readings:
            return 0.0

        # Get readings within the window
        now = datetime.utcnow()
        window_start = now - timedelta(hours=window_hours)

        window_readings = [
            r
            for r in readings
            if r.get("timestamp") and r.get("timestamp") >= window_start
        ]

        return sum(r.get("value", 0) for r in window_readings)

    def calculate_rate_of_change(
        self, current: float, previous: float, time_delta_hours: float
    ) -> float:
        """
        Compute rate of change in rainfall accumulation.

        Args:
            current: Current accumulation value
            previous: Previous accumulation value
            time_delta_hours: Time difference in hours

        Returns:
            Rate of change (mm/hour)
        """
        if time_delta_hours <= 0:
            return 0.0

        return (current - previous) / time_delta_hours

    def train_model(
        self, sensor_id: str, historical_data: pd.Series
    ) -> Optional[object]:
        """
        Train ARIMA model on historical rainfall data.

        Args:
            sensor_id: Sensor ID (for logging)
            historical_data: Pandas Series with datetime index and rainfall values

        Returns:
            Fitted ARIMA model or None if training fails
        """
        if not STATSMODELS_AVAILABLE:
            logger.warning(f"statsmodels not available for sensor {sensor_id}")
            return None

        if len(historical_data) < MIN_DATA_POINTS:
            logger.warning(
                f"Insufficient data for sensor {sensor_id}: "
                f"{len(historical_data)} points (need {MIN_DATA_POINTS})"
            )
            return None

        try:
            # Check for stationarity using Augmented Dickey-Fuller test
            adf_result = adfuller(historical_data.dropna())
            is_stationary = adf_result[1] < 0.05

            # Auto-select best ARIMA parameters using AIC criterion
            best_aic = np.inf
            best_model = None
            best_order = None

            # Try different parameter combinations
            for p in range(0, 3):
                for d in range(0, 2):
                    for q in range(0, 3):
                        try:
                            model = ARIMA(historical_data, order=(p, d, q))
                            fitted = model.fit()
                            if fitted.aic < best_aic:
                                best_aic = fitted.aic
                                best_model = fitted
                                best_order = (p, d, q)
                        except Exception as e:
                            logger.debug(
                                f"ARIMA({p},{d},{q}) failed for sensor {sensor_id}: {e}"
                            )
                            continue

            if best_model is None:
                logger.warning(f"Could not fit ARIMA model for sensor {sensor_id}")
                return None

            logger.info(
                f"Trained ARIMA{best_order} model for sensor {sensor_id} "
                f"(AIC: {best_aic:.2f})"
            )
            return best_model

        except Exception as e:
            logger.error(f"Error training ARIMA model for sensor {sensor_id}: {e}")
            return None

    def forecast_next_hour(
        self, model: object, current_readings: pd.Series
    ) -> Tuple[float, Dict]:
        """
        Predict rain accumulation for the next hour.

        Args:
            model: Fitted ARIMA model
            current_readings: Recent readings as Pandas Series

        Returns:
            Tuple of (forecast_value, forecast_confidence_dict)
        """
        if model is None:
            # Fallback: simple moving average
            if len(current_readings) > 0:
                forecast = current_readings.tail(6).mean()  # Last 6 hours average
                return forecast, {"method": "moving_average", "confidence": 0.5}
            return 0.0, {"method": "no_data", "confidence": 0.0}

        try:
            # Generate forecast
            forecast_result = model.forecast(steps=FORECAST_HORIZON)
            forecast_value = float(forecast_result.iloc[0])

            # Get confidence intervals if available
            try:
                conf_int = model.get_forecast(steps=FORECAST_HORIZON).conf_int()
                lower_bound = float(conf_int.iloc[0, 0])
                upper_bound = float(conf_int.iloc[0, 1])
                confidence_range = upper_bound - lower_bound
            except Exception:
                lower_bound = forecast_value * 0.8
                upper_bound = forecast_value * 1.2
                confidence_range = upper_bound - lower_bound

            return forecast_value, {
                "method": "arima",
                "confidence": min(
                    0.95,
                    max(0.5, 1.0 - (confidence_range / max(abs(forecast_value), 1))),
                ),
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
            }

        except Exception as e:
            logger.error(f"Error generating forecast: {e}")
            # Fallback to moving average
            if len(current_readings) > 0:
                forecast = current_readings.tail(6).mean()
                return forecast, {"method": "fallback_ma", "confidence": 0.4}
            return 0.0, {"method": "error", "confidence": 0.0}

    def detect_rapid_change(
        self,
        actual_rate: float,
        forecast_rate: float,
        historical_std: float,
        threshold: float = ANOMALY_THRESHOLD_MULTIPLIER,
    ) -> Dict:
        """
        Detect rapid rate of change in rainfall accumulation.

        Args:
            actual_rate: Current actual rate of change (mm/hour)
            forecast_rate: Forecasted rate of change (mm/hour)
            historical_std: Historical standard deviation of rates
            threshold: Multiplier for standard deviation threshold

        Returns:
            Dictionary with anomaly detection results
        """
        if historical_std <= 0:
            historical_std = 1.0  # Default to avoid division by zero

        deviation = actual_rate - forecast_rate
        threshold_value = threshold * historical_std

        if actual_rate > (forecast_rate + threshold_value):
            # Calculate severity based on deviation magnitude
            if actual_rate > forecast_rate + 3 * historical_std:
                severity = "critical"
                confidence = min(
                    0.95,
                    (actual_rate - forecast_rate) / (3 * historical_std),
                )
            elif actual_rate > forecast_rate + 2 * historical_std:
                severity = "high"
                confidence = min(
                    0.9,
                    (actual_rate - forecast_rate) / (2 * historical_std),
                )
            else:
                severity = "medium"
                confidence = min(
                    0.8,
                    (actual_rate - forecast_rate) / threshold_value,
                )

            return {
                "anomaly_detected": True,
                "severity": severity,
                "confidence": confidence,
                "actual_rate": actual_rate,
                "forecast_rate": forecast_rate,
                "deviation": deviation,
                "threshold": threshold_value,
            }

        return {
            "anomaly_detected": False,
            "actual_rate": actual_rate,
            "forecast_rate": forecast_rate,
        }

    async def analyze_rainfall_sensor(
        self, sensor_id: str, readings: List[Dict], db: AsyncIOMotorDatabase
    ) -> Dict:
        """
        Main analysis method that orchestrates the forecasting workflow.

        Args:
            sensor_id: Sensor ID to analyze
            readings: Current readings from the sensor
            db: Database connection

        Returns:
            Dictionary with risk assessment results
        """
        try:
            # Get historical data for training
            historical_readings = await self.get_historical_baseline(
                sensor_id, TRAINING_WINDOW_DAYS
            )

            if len(historical_readings) < MIN_DATA_POINTS:
                # Fallback to simple threshold detection
                logger.info(
                    f"Insufficient historical data for sensor {sensor_id}. "
                    f"Using threshold-based detection."
                )
                return self._fallback_threshold_detection(readings)

            # Resample to hourly intervals
            historical_series = self.resample_rainfall_data(historical_readings)

            # Train ARIMA model
            model = self.train_model(sensor_id, historical_series)

            # Prepare current readings for analysis
            current_series = self.resample_rainfall_data(readings)

            if len(current_series) < 2:
                logger.warning(f"Insufficient current readings for sensor {sensor_id}")
                return {
                    "anomaly_detected": False,
                    "reason": "insufficient_current_data",
                }

            # Calculate historical rates (hourly differences) for model training
            historical_rates = historical_series.diff().dropna()

            if len(historical_rates) < MIN_DATA_POINTS:
                logger.warning(
                    f"Insufficient rate data for sensor {sensor_id} after differencing"
                )
                return self._fallback_threshold_detection(readings)

            # Train model on rates instead of cumulative values
            rate_model = self.train_model(sensor_id, historical_rates)

            # Generate forecast for rate (mm/hour)
            forecast_rate, forecast_meta = self.forecast_next_hour(
                rate_model, historical_rates
            )

            # Calculate current accumulation rate (mm/hour)
            if len(current_series) >= 2:
                # Get last two hourly cumulative values
                recent_values = current_series.tail(2)
                if len(recent_values) == 2:
                    # Rate is the difference between consecutive hourly totals
                    current_rate = float(
                        recent_values.iloc[-1] - recent_values.iloc[-2]
                    )
                else:
                    # Fallback: use last value as rate estimate
                    current_rate = float(recent_values.iloc[-1])
            else:
                current_rate = (
                    float(current_series.iloc[-1]) if len(current_series) > 0 else 0.0
                )

            # Calculate historical statistics for comparison
            historical_mean = float(historical_rates.mean())
            historical_std = (
                float(historical_rates.std()) if len(historical_rates) > 1 else 1.0
            )

            # Detect anomalies
            anomaly_result = self.detect_rapid_change(
                actual_rate=current_rate,
                forecast_rate=forecast_rate,
                historical_std=max(historical_std, 0.1),  # Minimum std to avoid issues
            )

            if anomaly_result.get("anomaly_detected"):
                return {
                    "anomaly_detected": True,
                    "severity": anomaly_result["severity"],
                    "confidence": anomaly_result["confidence"],
                    "description": (
                        f"Abnormal rain accumulation detected: "
                        f"Current rate {current_rate:.2f} mm/h exceeds forecast "
                        f"{forecast_rate:.2f} mm/h by {anomaly_result['deviation']:.2f} mm/h. "
                        f"Threshold: {anomaly_result['threshold']:.2f} mm/h"
                    ),
                    "risk_type": "abnormal_rain_accumulation",
                    "forecast_data": {
                        "forecast_rate": forecast_rate,
                        "forecast_method": forecast_meta.get("method"),
                        "forecast_confidence": forecast_meta.get("confidence"),
                        "current_rate": current_rate,
                        "historical_mean": historical_mean,
                        "historical_std": historical_std,
                    },
                }

            return {
                "anomaly_detected": False,
                "forecast_data": {
                    "forecast_rate": forecast_rate,
                    "forecast_method": forecast_meta.get("method"),
                    "current_rate": current_rate,
                    "historical_mean": historical_mean,
                },
            }

        except Exception as e:
            logger.error(
                f"Error analyzing rainfall sensor {sensor_id}: {e}", exc_info=True
            )
            return {
                "anomaly_detected": False,
                "error": str(e),
                "reason": "analysis_error",
            }

    def _fallback_threshold_detection(self, readings: List[Dict]) -> Dict:
        """
        Fallback threshold-based detection when insufficient data for ARIMA.

        Args:
            readings: Current sensor readings

        Returns:
            Dictionary with threshold-based risk assessment
        """
        if not readings:
            return {"anomaly_detected": False, "reason": "no_data"}

        # Simple threshold: if recent readings show > 20mm/hour, flag as abnormal
        recent_readings = sorted(
            readings, key=lambda x: x.get("timestamp", datetime.min), reverse=True
        )[
            :6
        ]  # Last 6 readings

        if len(recent_readings) < 2:
            return {"anomaly_detected": False, "reason": "insufficient_data"}

        # Calculate rate from recent readings
        values = [r.get("value", 0) for r in recent_readings]
        timestamps = [
            r.get("timestamp")
            for r in recent_readings
            if r.get("timestamp") is not None
        ]

        if len(timestamps) < 2:
            return {"anomaly_detected": False, "reason": "invalid_timestamps"}

        time_delta = (timestamps[0] - timestamps[-1]).total_seconds() / 3600.0
        if time_delta <= 0:
            time_delta = 1.0

        rate = (values[0] - values[-1]) / time_delta

        # Threshold: 20 mm/hour is considered abnormal
        threshold = 20.0
        if rate > threshold:
            severity = "critical" if rate > 50.0 else "high"
            return {
                "anomaly_detected": True,
                "severity": severity,
                "confidence": min(0.8, rate / threshold),
                "description": (
                    f"High rain accumulation rate detected: {rate:.2f} mm/h "
                    f"(threshold: {threshold} mm/h)"
                ),
                "risk_type": "abnormal_rain_accumulation",
                "forecast_data": {
                    "current_rate": rate,
                    "method": "threshold_fallback",
                },
            }

        return {
            "anomaly_detected": False,
            "forecast_data": {"current_rate": rate, "method": "threshold_fallback"},
        }
