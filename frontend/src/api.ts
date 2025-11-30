import { httpClient, leaderboardApi } from './lib/httpClient';

export interface Asset {
    _id: string;
    feature_type: string;
    feature_code: string;
    geometry: {
        type: 'Point' | 'LineString' | 'Polygon' | 'MultiPoint' | 'MultiLineString' | 'MultiPolygon';
        coordinates: any; // GeoJSON coordinates can be number[], number[][], or number[][][]
    };
    created_at: string;
}

export interface MaintenanceLog {
    _id: string;
    asset_id: string;
    description: string;
    technician: string;
    status: string;
    scheduled_date: string;
    completed_date?: string;
    created_at: string;
}

export const getAssets = async () => {
    const response = await httpClient.get<Asset[]>('/assets');
    return response.data;
};

export interface LeaderboardEntry {
    msv: string;
    contributor_name: string;
    unit: string;
    count: number;
}

export const getLeaderboard = async () => {
    const response = await leaderboardApi.get<LeaderboardEntry[]>('/leaderboard');
    return response.data;
};

export const getMaintenanceLogs = async (assetId: string) => {
    const response = await httpClient.get<MaintenanceLog[]>(`/maintenance/asset/${assetId}`);
    return response.data;
};

export const createMaintenanceLog = async (data: any) => {
    const response = await httpClient.post('/maintenance', data);
    return response.data;
};

export default httpClient;
