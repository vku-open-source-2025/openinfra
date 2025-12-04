import { httpClient, leaderboardApi } from "./lib/httpClient";
import axios from "axios";

export const api = axios.create({
    baseURL: import.meta.env.VITE_BASE_API_URL || "/api",
});

export interface Asset {
    id: string;
    _id?: string; // Legacy support
    feature_type: string;
    feature_code: string;
    geometry: {
        type:
            | "Point"
            | "LineString"
            | "Polygon"
            | "MultiPoint"
            | "MultiLineString"
            | "MultiPolygon";
        coordinates: number[] | number[][] | number[][][]; // GeoJSON coordinates
    };
    created_at: string;
}

// Helper to get asset ID (supports both id and _id)
export const getAssetId = (asset: Asset): string => asset.id || asset._id || '';

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
    const response = await httpClient.get<Asset[]>("/assets/");
    return response.data;
};

export const loginAdmin = async (username: string, password: string) => {
    const response = await httpClient.post<{ access_token: string }>(
        "/auth/login",
        {
            username,
            password,
        }
    );
    return { token: response.data.access_token };
};

export interface LeaderboardEntry {
    msv: string;
    contributor_name: string;
    unit: string;
    count: number;
}

export const getLeaderboard = async () => {
    const response = await leaderboardApi.get<LeaderboardEntry[]>(
        "/leaderboard"
    );
    return response.data;
};

export const getMaintenanceLogs = async (assetId: string) => {
    const response = await httpClient.get<MaintenanceLog[]>(
        `/maintenance/asset/${assetId}`
    );
    return response.data;
};

export const createMaintenanceLog = async (data: Record<string, unknown>) => {
    const response = await httpClient.post("/maintenance", data);
    return response.data;
};

export default httpClient;
