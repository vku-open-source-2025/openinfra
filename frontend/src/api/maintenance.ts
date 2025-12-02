import { httpClient } from '../lib/httpClient';
import type {
  Maintenance,
  MaintenanceCreateRequest,
  MaintenanceUpdateRequest,
  MaintenanceStartRequest,
  MaintenanceCompleteRequest,
  MaintenanceApprovalRequest,
  MaintenanceFilterParams,
} from '../types/maintenance';
import { mockMaintenanceHistory, delay } from './mocks/assetLifecycleMocks';

// Set to true to use mock data instead of real API calls
const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === 'true' || false;

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

  getHistory: async (assetId: string, filters?: MaintenanceFilterParams): Promise<Maintenance[]> => {
    if (USE_MOCK_DATA) {
      await delay(400);
      let history = mockMaintenanceHistory(assetId);

      // Apply filters
      if (filters) {
        if (filters.date_from) {
          history = history.filter(m => new Date(m.scheduled_date) >= new Date(filters.date_from!));
        }
        if (filters.date_to) {
          history = history.filter(m => new Date(m.scheduled_date) <= new Date(filters.date_to!));
        }
        if (filters.technician) {
          history = history.filter(m => m.technician?.toLowerCase().includes(filters.technician!.toLowerCase()));
        }
        if (filters.cost_min !== undefined) {
          history = history.filter(m => (m.actual_cost || m.estimated_cost || 0) >= filters.cost_min!);
        }
        if (filters.cost_max !== undefined) {
          history = history.filter(m => (m.actual_cost || m.estimated_cost || 0) <= filters.cost_max!);
        }
        if (filters.approval_status) {
          history = history.filter(m => m.approval_status === filters.approval_status);
        }
      }

      return history;
    }
    const response = await httpClient.get<Maintenance[]>(`/maintenance/asset/${assetId}/history`, { params: filters });
    return response.data;
  },

  approve: async (id: string, data: MaintenanceApprovalRequest): Promise<Maintenance> => {
    const response = await httpClient.post<Maintenance>(`/maintenance/${id}/approve`, data);
    return response.data;
  },

  reject: async (id: string, reason: string): Promise<Maintenance> => {
    const response = await httpClient.post<Maintenance>(`/maintenance/${id}/reject`, { rejection_reason: reason });
    return response.data;
  },
};
