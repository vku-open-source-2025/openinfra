import axios from 'axios';

const api = axios.create({
    baseURL: import.meta.env.VITE_BASE_API_URL || '/api',
});

export interface Asset {
    _id: string;
    feature_type: string;
    feature_code: string;
    geometry: {
        type: string;
        coordinates: number[];
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
    const response = await api.get<Asset[]>('/assets/');
    return response.data;
};

export const getMaintenanceLogs = async (assetId: string) => {
    const response = await api.get<MaintenanceLog[]>(`/maintenance/asset/${assetId}`);
    return response.data;
};

export const createMaintenanceLog = async (data: any) => {
    const response = await api.post('/maintenance/', data);
    return response.data;
};

export default api;
