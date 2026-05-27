export type HazardSeverity = 'low' | 'medium' | 'high' | 'critical';

export type HazardEventType =
  | 'flood'
  | 'storm'
  | 'landslide'
  | 'fire'
  | 'earthquake'
  | 'outage'
  | 'pollution'
  | 'drought'
  | 'traffic'
  | 'epidemic'
  | 'infrastructure_failure'
  | 'other';

export type HazardSource = 'nchmf' | 'vndms' | 'manual' | 'iot' | 'other';

export interface HazardGeometry {
  type: string;
  coordinates: unknown;
}

export interface Hazard {
  id: string;
  hazard_id: string;
  title: string;
  description?: string;
  event_type: HazardEventType;
  severity: HazardSeverity;
  source: HazardSource;
  is_active: boolean;
  geometry: HazardGeometry;
  district?: string;
  ward?: string;
  metadata: Record<string, unknown>;
  detected_at?: string;
  ingest_timestamp?: string;
  issued_at?: string;
  expires_at?: string;
  last_seen_at?: string;
  created_at: string;
  updated_at: string;
}

export interface RecentHazardItem {
  id: string;
  hazard_id: string;
  title: string;
  event_type: HazardEventType;
  severity: HazardSeverity;
  source: HazardSource;
  geometry?: HazardGeometry;
  district?: string;
  ward?: string;
  detected_at?: string;
  expires_at?: string;
  /** linked_event_id is populated if this hazard has been deployed as an emergency event */
  linked_event_id?: string | null;
  linked_eop_plan_id?: string | null;
}

export interface HazardListParams {
  skip?: number;
  limit?: number;
  is_active?: boolean;
  event_type?: string;
  severity?: string;
  source?: string;
  district?: string;
  ward?: string;
}
