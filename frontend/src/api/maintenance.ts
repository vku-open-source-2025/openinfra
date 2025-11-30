import { httpClient } from '../lib/httpClient';
import type {
  Maintenance,
  MaintenanceCreateRequest,
  MaintenanceUpdateRequest,
  MaintenanceStartRequest,
  MaintenanceCompleteRequest,
} from '../types/maintenance';

export interface MaintenanceListParams {
  skip?: number;
  limit?: number;
  asset_id?: string;
  status?: string;
  assigned_to?: string;
  priority?: string;
}

export const maintenanceApi = {
  list: async (params?: MaintenanceListParams): Promise<Maintenance[]> => {
    const response = await httpClient.get<Maintenance[]>('/maintenance', { params });
    return response.data;
  },

  getUpcoming: async (days?: number): Promise<Maintenance[]> => {
    const response = await httpClient.get<Maintenance[]>('/maintenance/upcoming', {
      params: days ? { days } : undefined,
    });
    return response.data;
  },

  getById: async (id: string): Promise<Maintenance> => {
    const response = await httpClient.get<Maintenance>(`/maintenance/${id}`);
    return response.data;
  },

  create: async (data: MaintenanceCreateRequest): Promise<Maintenance> => {
    const response = await httpClient.post<Maintenance>('/maintenance', data);
    return response.data;
  },

  update: async (id: string, data: MaintenanceUpdateRequest): Promise<Maintenance> => {
    const response = await httpClient.put<Maintenance>(`/maintenance/${id}`, data);
    return response.data;
  },

  assign: async (id: string, assignedTo: string): Promise<Maintenance> => {
    const response = await httpClient.post<Maintenance>(`/maintenance/${id}/assign`, null, {
      params: { assigned_to: assignedTo },
    });
    return response.data;
  },

  start: async (id: string, data?: MaintenanceStartRequest): Promise<Maintenance> => {
    const response = await httpClient.post<Maintenance>(`/maintenance/${id}/start`, data);
    return response.data;
  },

  complete: async (id: string, data: MaintenanceCompleteRequest): Promise<Maintenance> => {
    const response = await httpClient.post<Maintenance>(`/maintenance/${id}/complete`, data);
    return response.data;
  },

  cancel: async (id: string, cancellationReason: string): Promise<Maintenance> => {
    const response = await httpClient.post<Maintenance>(`/maintenance/${id}/cancel`, null, {
      params: { cancellation_reason: cancellationReason },
    });
    return response.data;
  },

  uploadPhotos: async (id: string, files: File[], photoType: 'before' | 'after' = 'after'): Promise<Maintenance> => {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });
    const response = await httpClient.post<Maintenance>(`/maintenance/${id}/photos`, formData, {
      params: { photo_type: photoType },
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  getByAsset: async (assetId: string, params?: { skip?: number; limit?: number }): Promise<Maintenance[]> => {
    const response = await httpClient.get<Maintenance[]>(`/maintenance/asset/${assetId}`, { params });
    return response.data;
  },
};
