export type IncidentStatus = 'reported' | 'acknowledged' | 'assigned' | 'in_progress' | 'resolved' | 'closed';
export type IncidentSeverity = 'low' | 'medium' | 'high' | 'critical';
export type ReporterType = 'citizen' | 'technician' | 'admin' | 'manager';

export interface IncidentLocation {
  address?: string;
  geometry?: {
    type: string;
    coordinates: number[] | number[][] | number[][][];
  };
  coordinates?: {
    longitude: number;
    latitude: number;
  };
}

export interface IncidentComment {
  id: string;
  comment: string;
  user_id?: string;
  user_name?: string;
  is_internal: boolean;
  created_at: string;
}

export interface Incident {
  id: string;
  incident_code: string;
  title: string;
  description: string;
  severity: IncidentSeverity;
  status: IncidentStatus;
  asset_id?: string;
  location?: IncidentLocation;
  reported_by?: string;
  reporter_type: ReporterType;
  assigned_to?: string;
  upvotes: number;
  comments: IncidentComment[];
  created_at: string;
  updated_at: string;
}

export interface IncidentCreateRequest {
  title: string;
  description: string;
  severity: IncidentSeverity;
  asset_id?: string;
  location: IncidentLocation;
}

export interface IncidentUpdateRequest {
  title?: string;
  description?: string;
  severity?: IncidentSeverity;
  status?: IncidentStatus;
  assigned_to?: string;
}

export interface IncidentCommentRequest {
  comment: string;
  is_internal?: boolean;
}
