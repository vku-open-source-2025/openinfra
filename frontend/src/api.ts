import { httpClient, leaderboardApi } from "./lib/httpClient";
import axios from "axios";

export const api = axios.create({
    baseURL: import.meta.env.VITE_BASE_API_URL || "/api",
});

export interface Asset {
    _id: string;
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
    const response = await httpClient.get<Asset[]>("/assets");
    return response.data;
};

export const loginAdmin = async (username: string, password: string) => {
    const response = await api.post<{ token: string }>("/auth/login", {
        username,
        password,
    });
    return response.data;
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

export const IncidentCategory = {
    DAMAGE: "damage",
    MALFUNCTION: "malfunction",
    SAFETY_HAZARD: "safety_hazard",
    VANDALISM: "vandalism",
    OTHER: "other",
} as const;
export type IncidentCategory = typeof IncidentCategory[keyof typeof IncidentCategory];

export const IncidentSeverity = {
    LOW: "low",
    MEDIUM: "medium",
    HIGH: "high",
    CRITICAL: "critical",
} as const;
export type IncidentSeverity = typeof IncidentSeverity[keyof typeof IncidentSeverity];

export interface IncidentCreate {
    asset_id?: string;
    title: string;
    description: string;
    category: IncidentCategory;
    severity: IncidentSeverity;
    reported_via?: string;
    public_visible?: boolean;
}

export const createIncident = async (data: IncidentCreate) => {
    const response = await httpClient.post("/incidents", data);
    return response.data;
};

export default httpClient;
