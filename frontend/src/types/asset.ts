export type AssetStatus = 'active' | 'inactive' | 'maintenance' | 'decommissioned';

export interface AssetGeometry {
  type: 'Point' | 'LineString' | 'Polygon' | 'MultiPoint' | 'MultiLineString' | 'MultiPolygon';
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
}
