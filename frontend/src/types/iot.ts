export type SensorStatus = 'active' | 'inactive' | 'maintenance';
export type SensorType = 'temperature' | 'humidity' | 'pressure' | 'vibration' | 'noise' | 'air_quality' | 'other';

export interface SensorLocation {
  longitude: number;
  latitude: number;
}

export interface SensorThresholds {
  warning_min?: number;
  warning_max?: number;
  critical_min?: number;
  critical_max?: number;
}

export interface IoTSensor {
  id: string;
  sensor_code: string;
  asset_id: string;
  sensor_type: SensorType;
  status: SensorStatus;
  location: SensorLocation;
  measurement_unit?: string;
  thresholds?: SensorThresholds;
  last_seen?: string;
  last_reading?: number | { value: number; timestamp: string; status: string };
  created_at: string;
}

export interface SensorReading {
  sensor_id: string;
  timestamp: string;
  value: number;
  metadata?: Record<string, any>;
}

export interface SensorStatistics {
  sensor_id: string;
  granularity: 'minute' | 'hour' | 'day';
  data: Array<{
    timestamp: string;
    avg: number;
    min: number;
    max: number;
    count: number;
  }>;
}

export interface SensorCreateRequest {
  sensor_code: string;
  asset_id: string;
  sensor_type: SensorType;
  location: SensorLocation;
  measurement_unit?: string;
  thresholds?: SensorThresholds;
}

export interface SensorUpdateRequest {
  sensor_type?: SensorType;
  status?: SensorStatus;
  location?: SensorLocation;
  measurement_unit?: string;
  thresholds?: SensorThresholds;
}

export interface SensorReadingIngestRequest {
  timestamp?: string;
  value: number;
  metadata?: Record<string, any>;
}
