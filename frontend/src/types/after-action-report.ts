export type AfterActionStatus = 'draft' | 'published' | 'archived';

export interface AfterActionTimelineEntry {
  timestamp: string;
  source: string;
  action: string;
  details: Record<string, unknown>;
}

export interface AfterActionKPI {
  response_time_minutes?: number;
  response_speed_score: number;
  dispatch_completion_rate: number;
  sitrep_coverage_rate: number;
  resource_efficiency_score: number;
  overall_score: number;
}

export interface AfterActionReport {
  id: string;
  report_code: string;
  emergency_event_id: string;
  title: string;
  summary: string;
  status: AfterActionStatus;
  timeline: AfterActionTimelineEntry[];
  kpi: AfterActionKPI;
  lessons_learned: string[];
  recommendations: string[];
  generated_by?: string;
  published_by?: string;
  generated_at: string;
  published_at?: string;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface AfterActionGenerateRequest {
  emergency_event_id: string;
  title?: string;
  summary_override?: string;
  lessons_learned?: string[];
  recommendations?: string[];
  force_regenerate?: boolean;
  metadata?: Record<string, unknown>;
}

export interface AfterActionUpdateRequest {
  title?: string;
  summary?: string;
  lessons_learned?: string[];
  recommendations?: string[];
  status?: AfterActionStatus;
  metadata?: Record<string, unknown>;
}
