export type IncidentStatus = 'reported' | 'acknowledged' | 'assigned' | 'investigating' | 'in_progress' | 'waiting_approval' | 'resolved' | 'closed';
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

export interface AssetSummary {
  id: string;
  asset_code?: string;
  name?: string;
  feature_type: string;
  category?: string;
  status?: string;
}

export interface IncidentComment {
  id: string;
  comment: string;
  user_id?: string;
  user_name?: string;
  is_internal: boolean;
  posted_at: string;
  created_at?: string; // For backwards compatibility
}

export interface Incident {
  id: string;
  incident_code: string;
  title: string;
  description: string;
  severity: IncidentSeverity;
  status: IncidentStatus;
  asset_id?: string;
  asset?: AssetSummary;
  location?: IncidentLocation;
  reported_by?: string;
  reporter_type: ReporterType;
  assigned_to?: string;
  maintenance_record_id?: string;
  resolution_type?: string;
  resolution_notes?: string;
  cost_status?: 'pending' | 'approved' | 'rejected';
  photos?: string[];
  upvotes: number;
  comments: IncidentComment[];
  created_at: string;
  updated_at: string;
  // AI Verification
  ai_verification_status?: 'pending' | 'verified' | 'to_be_verified' | 'failed';
  ai_confidence_score?: number;
  ai_verification_reason?: string;
  ai_verified_at?: string;
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
