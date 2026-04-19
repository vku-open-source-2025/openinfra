export type ResourceType =
  | 'personnel'
  | 'vehicle'
  | 'medical_supply'
  | 'rescue_equipment'
  | 'shelter';

export type ResourceStatus =
  | 'available'
  | 'deployed'
  | 'standby'
  | 'offline'
  | 'maintenance';

export interface ResourceUnit {
  id: string;
  resource_code: string;
  name: string;
  resource_type: ResourceType;
  status: ResourceStatus;
  capacity?: number;
  capacity_unit?: string;
  district?: string;
  ward?: string;
  current_location?: {
    type: string;
    coordinates: number[] | number[][] | number[][][];
  };
  skills: string[];
  contact_phone?: string;
  assigned_dispatch_order_id?: string;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ResourceUnitCreateRequest {
  resource_code: string;
  name: string;
  resource_type: ResourceType;
  status?: ResourceStatus;
  capacity?: number;
  capacity_unit?: string;
  district?: string;
  ward?: string;
  current_location?: {
    type: string;
    coordinates: number[] | number[][] | number[][][];
  };
  skills?: string[];
  contact_phone?: string;
  metadata?: Record<string, unknown>;
}

export interface ResourceUnitUpdateRequest {
  name?: string;
  resource_type?: ResourceType;
  status?: ResourceStatus;
  capacity?: number;
  capacity_unit?: string;
  district?: string;
  ward?: string;
  current_location?: {
    type: string;
    coordinates: number[] | number[][] | number[][][];
  };
  skills?: string[];
  contact_phone?: string;
  assigned_dispatch_order_id?: string;
  metadata?: Record<string, unknown>;
}
