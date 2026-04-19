export type EmergencyEventType =
  | 'flood'
  | 'storm'
  | 'landslide'
  | 'fire'
  | 'earthquake'
  | 'outage'
  | 'pollution'
  | 'other';

export type EmergencySeverity = 'low' | 'medium' | 'high' | 'critical';

export type EmergencyStatus =
  | 'monitoring'
  | 'active'
  | 'contained'
  | 'resolved'
  | 'canceled';

export type EmergencySource = 'manual' | 'iot' | 'forecast' | 'sosconn' | 'other';

export interface EmergencyLocation {
  geometry?: {
    type: string;
    coordinates: number[] | number[][] | number[][][];
  };
  address?: string;
  ward?: string;
  district?: string;
  city?: string;
}

export interface EmergencyEvent {
  id: string;
  event_code?: string;
  title: string;
  description?: string;
  event_type: EmergencyEventType;
  severity: EmergencySeverity;
  status: EmergencyStatus;
  source: EmergencySource;
  location?: EmergencyLocation;
  affected_asset_ids: string[];
  affected_area_km2?: number;
  estimated_impact: Record<string, unknown>;
  instructions: string[];
  tags: string[];
  started_at?: string;
  ended_at?: string;
  created_by?: string;
  updated_by?: string;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface EmergencyEventCreateRequest {
  title: string;
  description?: string;
  event_type: EmergencyEventType;
  severity: EmergencySeverity;
  source?: EmergencySource;
  location?: EmergencyLocation;
  affected_asset_ids?: string[];
  affected_area_km2?: number;
  estimated_impact?: Record<string, unknown>;
  instructions?: string[];
  tags?: string[];
  started_at?: string;
  metadata?: Record<string, unknown>;
}

export interface EmergencyEventUpdateRequest {
  title?: string;
  description?: string;
  event_type?: EmergencyEventType;
  severity?: EmergencySeverity;
  status?: EmergencyStatus;
  source?: EmergencySource;
  location?: EmergencyLocation;
  affected_asset_ids?: string[];
  affected_area_km2?: number;
  estimated_impact?: Record<string, unknown>;
  instructions?: string[];
  tags?: string[];
  started_at?: string;
  ended_at?: string;
  metadata?: Record<string, unknown>;
}
