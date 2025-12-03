export type AssetStatus =
    | "active"
    | "inactive"
    | "maintenance"
    | "decommissioned";
export type LifecycleStatus =
    | "operational"
    | "under_repair"
    | "damaged"
    | "decommissioned";

export interface AssetGeometry {
    type:
        | "Point"
        | "LineString"
        | "Polygon"
        | "MultiPoint"
        | "MultiLineString"
        | "MultiPolygon";
    coordinates: number[] | number[][] | number[][][];
}

export interface AssetLocation {
    address: string;
    ward?: string;
    district?: string;
    city?: string | null;
    country?: string;
}

export interface AssetAttachment {
    file_name: string;
    file_url: string;
    file_type: string;
    uploaded_by: string;
    uploaded_at: string;
    version?: number;
    is_public?: boolean;
    document_type?: string;
}

export interface AssetLifecycleData {
    lifecycle_status: LifecycleStatus;
    health_score: number; // 0-100
    remaining_lifespan_years?: number;
    commissioned_date?: string;
    designed_lifespan_years?: number;
    last_maintenance_date?: string;
    next_maintenance_date?: string;
    maintenance_overdue?: boolean;
}

export interface AssetSpecifications {
    manufacturer?: string | null;
    model?: string | null;
    serial_number?: string | null;
    installation_date?: string | null;
    warranty_expiry?: string | null;
    capacity?: string | null;
    dimensions?: string | null;
    weight?: string | null;
    material?: string | null;
    custom_fields?: Record<string, unknown>;
}

export interface Asset {
    id: string;
    asset_code: string;
    name: string;
    feature_type: string;
    feature_code: string;
    geometry: AssetGeometry;
    category?: string;
    status: AssetStatus;
    condition?: string;
    lifecycle_stage?: string;
    location: AssetLocation;
    specifications?: AssetSpecifications;
    properties?: Record<string, unknown>;
    attachments?: AssetAttachment[];
    lifecycle?: AssetLifecycleData;
    managing_unit?: string;
    manufacturer?: string;
    installation_cost?: number | null;
    current_value?: number | null;
    depreciation_rate?: number | null;
    owner?: string | null;
    manager_id?: string | null;
    qr_code?: string | null;
    nfc_tag_id?: string | null;
    public_info_visible?: boolean;
    iot_enabled?: boolean;
    sensor_ids?: string[];
    tags?: string[];
    notes?: string | null;
    created_at: string;
    updated_at: string;
    created_by?: string;
    updated_by?: string | null;
}

export interface AssetCreateRequest {
    asset_code: string;
    name: string;
    feature_type: string;
    feature_code: string;
    geometry: AssetGeometry;
    category?: string;
    status?: AssetStatus;
    location?: AssetLocation;
    specifications?: Partial<AssetSpecifications>;
    condition?: string;
    lifecycle_stage?: string;
    properties?: Record<string, unknown>;
}

export interface AssetUpdateRequest {
    name?: string;
    feature_type?: string;
    category?: string;
    status?: AssetStatus;
    location?: AssetLocation;
    properties?: Record<string, unknown>;
    lifecycle_status?: LifecycleStatus;
    managing_unit?: string;
    manufacturer?: string;
    commissioned_date?: string;
    designed_lifespan_years?: number;
}
