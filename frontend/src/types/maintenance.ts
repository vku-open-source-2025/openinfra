export type MaintenanceStatus = 'scheduled' | 'in_progress' | 'completed' | 'cancelled';
export type MaintenancePriority = 'low' | 'medium' | 'high' | 'urgent';

export interface Maintenance {
  id: string;
  work_order_number: string;
  asset_id: string;
  title: string;
  description: string;
  priority: MaintenancePriority;
  status: MaintenanceStatus;
  scheduled_date: string;
  started_at?: string;
  completed_at?: string;
  assigned_to?: string;
  technician?: string;
  estimated_cost?: number;
  actual_cost?: number;
  created_at: string;
  updated_at: string;
}

export interface MaintenanceCreateRequest {
  asset_id: string;
  title: string;
  description: string;
  priority: MaintenancePriority;
  scheduled_date: string;
  estimated_cost?: number;
  technician?: string;
}

export interface MaintenanceUpdateRequest {
  title?: string;
  description?: string;
  priority?: MaintenancePriority;
  status?: MaintenanceStatus;
  scheduled_date?: string;
  assigned_to?: string;
  estimated_cost?: number;
  actual_cost?: number;
}

export interface MaintenanceStartRequest {
  actual_start_time?: string;
}

export interface MaintenanceCompleteRequest {
  completion_notes: string;
  actual_cost?: number;
  quality_checks?: any[];
}
