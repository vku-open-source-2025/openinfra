export type AlertStatus = 'active' | 'acknowledged' | 'resolved' | 'dismissed';
export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical';

export interface Alert {
  id: string;
  alert_type: string;
  severity: AlertSeverity;
  status: AlertStatus;
  asset_id?: string;
  sensor_id?: string;
  message: string;
  metadata: Record<string, any>;
  acknowledged_at?: string;
  resolved_at?: string;
  created_at: string;
}

export interface AlertResolveRequest {
  resolution_notes?: string;
}
