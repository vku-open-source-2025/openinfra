export type MaintenanceStatus =
    | "scheduled"
    | "in_progress"
    | "completed"
    | "cancelled";
export type MaintenancePriority = "low" | "medium" | "high" | "urgent";
export type MaintenanceType =
    | "preventive"
    | "corrective"
    | "predictive"
    | "emergency";
export type MaintenanceApprovalStatus = "pending" | "approved" | "rejected";

export interface Maintenance {
    id: string;
    work_order_number: string;
    asset_id: string;
    title: string;
    description: string;
    priority: MaintenancePriority;
    status: MaintenanceStatus;
    type?: MaintenanceType;
    scheduled_date: string;
    started_at?: string;
    completed_at?: string;
    assigned_to?: string;
    technician?: string;
    estimated_cost?: number;
    actual_cost?: number;
    approval_status?: MaintenanceApprovalStatus;
    rejection_reason?: string;
    parts_replaced?: string[];
    notes?: string;
    attachments?: Array<{
        file_name: string;
        file_url: string;
        file_type: string;
        uploaded_at: string;
    }>;
    created_at: string;
    updated_at: string;
}

export interface MaintenanceCreateRequest {
    asset_id: string;
    title: string;
    description: string;
    priority: MaintenancePriority;
    type?: MaintenanceType;
    scheduled_date: string;
    estimated_cost?: number;
    actual_cost?: number;
    technician?: string;
    parts_replaced?: string[];
    notes?: string;
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
    work_performed: string; // Required: Description of work performed
    completion_notes?: string; // Optional: Additional completion notes
    actual_cost?: number;
    quality_checks?: any[];
}

export interface MaintenanceApprovalRequest {
    approval_status: "approved" | "rejected";
    rejection_reason?: string;
}

export interface MaintenanceFilterParams {
    asset_id?: string;
    technician?: string;
    status?: MaintenanceStatus;
    type?: MaintenanceType;
    approval_status?: MaintenanceApprovalStatus;
    date_from?: string;
    date_to?: string;
    cost_min?: number;
    cost_max?: number;
    skip?: number;
    limit?: number;
}
