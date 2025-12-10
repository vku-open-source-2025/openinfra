/**
 * Health Score Calculation Utilities
 *
 * Note: Actual calculation should be done on the backend.
 * These utilities are for frontend display and validation.
 */

export interface HealthScoreFactors {
  incident_frequency: number; // 0-100
  incident_severity: number; // 0-100
  maintenance_recency: number; // 0-100 (days since last maintenance)
  maintenance_cost_trend: number; // 0-100 (cost trend analysis)
  iot_sensor_alerts?: number; // 0-100 (if IoT available)
}

export interface HealthScoreCalculation {
  score: number; // 0-100
  factors: HealthScoreFactors;
  breakdown: {
    incident_frequency_weight: number;
    incident_severity_weight: number;
    maintenance_recency_weight: number;
    maintenance_cost_trend_weight: number;
    iot_weight?: number;
  };
}

/**
 * Calculate health score from factors
 * This is a frontend approximation - backend should do the real calculation
 */
export function calculateHealthScore(factors: HealthScoreFactors): number {
  const weights = {
    incident_frequency: 0.25,
    incident_severity: 0.25,
    maintenance_recency: 0.20,
    maintenance_cost_trend: 0.15,
    iot_sensor_alerts: 0.15,
  };

  let totalWeight = weights.incident_frequency + weights.incident_severity +
                    weights.maintenance_recency + weights.maintenance_cost_trend;

  let score =
    factors.incident_frequency * weights.incident_frequency +
    factors.incident_severity * weights.incident_severity +
    factors.maintenance_recency * weights.maintenance_recency +
    factors.maintenance_cost_trend * weights.maintenance_cost_trend;

  if (factors.iot_sensor_alerts !== undefined) {
    score += factors.iot_sensor_alerts * weights.iot_sensor_alerts;
  } else {
    // Redistribute IoT weight proportionally if not available
    const adjustedWeights = {
      incident_frequency: weights.incident_frequency / totalWeight,
      incident_severity: weights.incident_severity / totalWeight,
      maintenance_recency: weights.maintenance_recency / totalWeight,
      maintenance_cost_trend: weights.maintenance_cost_trend / totalWeight,
    };
    score =
      factors.incident_frequency * adjustedWeights.incident_frequency +
      factors.incident_severity * adjustedWeights.incident_severity +
      factors.maintenance_recency * adjustedWeights.maintenance_recency +
      factors.maintenance_cost_trend * adjustedWeights.maintenance_cost_trend;
  }

  return Math.round(Math.max(0, Math.min(100, score)));
}

/**
 * Get health score color based on score value
 */
export function getHealthScoreColor(score: number): string {
  if (score >= 80) return 'green';
  if (score >= 60) return 'yellow';
  if (score >= 40) return 'orange';
  return 'red';
}

/**
 * Get health score label
 */
export function getHealthScoreLabel(score: number): string {
  if (score >= 80) return 'Xuất sắc';
  if (score >= 60) return 'Tốt';
  if (score >= 40) return 'Trung bình';
  if (score >= 20) return 'Kém';
  return 'Nguy kịch';
}

/**
 * Calculate remaining lifespan percentage
 */
export function calculateRemainingLifespan(
  currentAge: number,
  designedLifespan: number
): number {
  if (designedLifespan <= 0) return 0;
  const remaining = Math.max(0, designedLifespan - currentAge);
  return Math.round((remaining / designedLifespan) * 100);
}

/**
 * Check if maintenance is overdue
 */
export function isMaintenanceOverdue(nextMaintenanceDate: string): boolean {
  const nextDate = new Date(nextMaintenanceDate);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return nextDate < today;
}

/**
 * Check if maintenance is due soon (within warning window)
 */
export function isMaintenanceDueSoon(
  nextMaintenanceDate: string,
  warningDays: number = 7
): boolean {
  const nextDate = new Date(nextMaintenanceDate);
  const today = new Date();
  const warningDate = new Date(today);
  warningDate.setDate(today.getDate() + warningDays);
  return nextDate <= warningDate && nextDate >= today;
}
