export interface PreventiveMaintenancePlan {
  id: string;
  asset_id: string;
  cycle_days: number; // e.g., 180 for 6 months
  cycle_description?: string; // e.g., "Every 6 months"
  last_maintenance_date?: string;
  next_maintenance_date: string;
  warning_days?: number; // Days before due date to show warning (default: 7)
  responsible_team?: string;
  assigned_technician?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PreventiveMaintenancePlanCreateRequest {
  asset_id: string;
  cycle_days: number;
  cycle_description?: string;
  warning_days?: number;
  responsible_team?: string;
  assigned_technician?: string;
}

export interface PreventiveMaintenancePlanUpdateRequest {
  cycle_days?: number;
  cycle_description?: string;
  warning_days?: number;
  responsible_team?: string;
  assigned_technician?: string;
  is_active?: boolean;
}

export interface PreventiveMaintenanceTask {
  id: string;
  asset_id: string;
  plan_id: string;
  scheduled_date: string;
  status: 'upcoming' | 'due_soon' | 'overdue' | 'completed';
  completed_date?: string;
  maintenance_record_id?: string;
}
