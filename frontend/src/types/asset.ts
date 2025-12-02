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
    coordinates: {
        longitude: number;
        latitude: number;
    };
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

export interface Asset {
    id: string;
    asset_code: string;
    name: string;
    feature_type: string;
    feature_code: string;
    geometry: AssetGeometry;
    category?: string;
    status: AssetStatus;
    location: AssetLocation;
    properties?: Record<string, any>;
    attachments?: AssetAttachment[];
    lifecycle?: AssetLifecycleData;
    managing_unit?: string;
    manufacturer?: string;
    created_at: string;
    updated_at: string;
}

export interface AssetCreateRequest {
    asset_code: string;
    name: string;
    feature_type: string;
    feature_code: string;
    geometry: AssetGeometry;
    category?: string;
    status?: AssetStatus;
    location: AssetLocation;
    properties?: Record<string, any>;
}

export interface AssetUpdateRequest {
    name?: string;
    feature_type?: string;
    category?: string;
    status?: AssetStatus;
    location?: AssetLocation;
    properties?: Record<string, any>;
    lifecycle_status?: LifecycleStatus;
    managing_unit?: string;
    manufacturer?: string;
    commissioned_date?: string;
    designed_lifespan_years?: number;
}
