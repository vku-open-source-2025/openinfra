export type EOPPlanStatus =
  | 'draft'
  | 'review_pending'
  | 'approved'
  | 'published'
  | 'archived';

export interface EOPAction {
  action_id: string;
  title: string;
  description?: string;
  phase: string;
  priority: string;
  owner_role?: string;
  estimated_minutes?: number;
  dependencies: string[];
}

export interface EOPAssignment {
  action_id: string;
  resource_unit_id?: string;
  assignee_id?: string;
  status: string;
  notes?: string;
}

export interface EOPPlan {
  id: string;
  emergency_event_id: string;
  version: number;
  title: string;
  summary?: string;
  objectives: string[];
  operational_phases: string[];
  actions: EOPAction[];
  assignment_matrix: EOPAssignment[];
  evacuation_plan: string[];
  fallback_plan: string[];
  communications_plan: string[];
  status: EOPPlanStatus;
  review_notes?: string;
  approved_by?: string;
  approved_at?: string;
  published_by?: string;
  published_at?: string;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface EOPPlanCreateRequest {
  emergency_event_id: string;
  title: string;
  summary?: string;
  objectives?: string[];
  operational_phases?: string[];
  actions?: EOPAction[];
  assignment_matrix?: EOPAssignment[];
  evacuation_plan?: string[];
  fallback_plan?: string[];
  communications_plan?: string[];
  metadata?: Record<string, unknown>;
}

export interface EOPGenerateRequest {
  emergency_event_id: string;
  additional_context?: string;
  force_new_version?: boolean;
}

export interface EOPPlanUpdateRequest {
  title?: string;
  summary?: string;
  objectives?: string[];
  operational_phases?: string[];
  actions?: EOPAction[];
  assignment_matrix?: EOPAssignment[];
  evacuation_plan?: string[];
  fallback_plan?: string[];
  communications_plan?: string[];
  review_notes?: string;
  metadata?: Record<string, unknown>;
}
