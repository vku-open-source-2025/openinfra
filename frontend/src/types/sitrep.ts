export type SitrepStatus = 'draft' | 'published' | 'archived';

export interface SitrepDelta {
  actor_id?: string;
  action_type: string;
  changes: Record<string, unknown>;
  created_at?: string;
}

export interface Sitrep {
  id: string;
  emergency_event_id: string;
  title: string;
  snapshot: Record<string, unknown>;
  deltas: SitrepDelta[];
  status: SitrepStatus;
  published_by?: string;
  published_at?: string;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface SitrepCreateRequest {
  emergency_event_id: string;
  title: string;
  snapshot?: Record<string, unknown>;
  deltas?: SitrepDelta[];
  metadata?: Record<string, unknown>;
}

export interface SitrepUpdateRequest {
  title?: string;
  snapshot?: Record<string, unknown>;
  status?: SitrepStatus;
  metadata?: Record<string, unknown>;
}
