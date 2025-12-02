import { httpClient } from '../lib/httpClient';
import type { Asset, AssetCreateRequest, AssetUpdateRequest, AssetLifecycleData, LifecycleStatus, AssetAttachment } from '../types/asset';
import { mockAssetWithLifecycle, mockHealthScore, mockDocuments, delay } from './mocks/assetLifecycleMocks';

// Set to true to use mock data instead of real API calls
const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === 'true' || false;

export interface AssetListParams {
  skip?: number;
  limit?: number;
  feature_type?: string;
  status?: string;
  category?: string;
}

export const assetsApi = {
  list: async (params?: AssetListParams): Promise<Asset[]> => {
    const response = await httpClient.get<Asset[]>('/assets', { params });
    return response.data;
  },

  getById: async (id: string): Promise<Asset> => {
    const response = await httpClient.get<Asset>(`/assets/${id}`);
    return response.data;
  },

  create: async (data: AssetCreateRequest): Promise<Asset> => {
    const response = await httpClient.post<Asset>('/assets', data);
    return response.data;
  },

  update: async (id: string, data: AssetUpdateRequest): Promise<Asset> => {
    const response = await httpClient.put<Asset>(`/assets/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await httpClient.delete(`/assets/${id}`);
  },

  getHistory: async (id: string, limit?: number): Promise<{ data: any[]; count: number }> => {
    const response = await httpClient.get<{ data: any[]; count: number }>(`/assets/${id}/history`, {
      params: limit ? { limit } : undefined,
    });
    return response.data;
  },

  uploadPhoto: async (id: string, file: File): Promise<Asset> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await httpClient.post<Asset>(`/assets/${id}/photos`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  uploadAttachment: async (id: string, file: File): Promise<Asset> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await httpClient.post<Asset>(`/assets/${id}/attachments`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  deleteAttachment: async (id: string, attachmentUrl: string): Promise<void> => {
    await httpClient.delete(`/assets/${id}/attachments/${encodeURIComponent(attachmentUrl)}`);
  },

  getAssetWithLifecycle: async (id: string): Promise<Asset> => {
    if (USE_MOCK_DATA) {
      await delay(500); // Simulate network delay
      return mockAssetWithLifecycle(id);
    }
    const response = await httpClient.get<Asset>(`/assets/${id}/lifecycle`);
    return response.data;
  },

  updateLifecycleStatus: async (id: string, status: LifecycleStatus): Promise<Asset> => {
    const response = await httpClient.put<Asset>(`/assets/${id}/lifecycle-status`, { lifecycle_status: status });
    return response.data;
  },

  getHealthScore: async (id: string): Promise<{ health_score: number; factors: any }> => {
    if (USE_MOCK_DATA) {
      await delay(300);
      return mockHealthScore(id);
    }
    const response = await httpClient.get<{ health_score: number; factors: any }>(`/assets/${id}/health-score`);
    return response.data;
  },

  getDocuments: async (id: string): Promise<AssetAttachment[]> => {
    if (USE_MOCK_DATA) {
      await delay(300);
      return mockDocuments(id);
    }
    const response = await httpClient.get<AssetAttachment[]>(`/assets/${id}/documents`);
    return response.data;
  },

  uploadDocument: async (id: string, file: File, documentType?: string, isPublic?: boolean): Promise<AssetAttachment> => {
    const formData = new FormData();
    formData.append('file', file);
    if (documentType) formData.append('document_type', documentType);
    if (isPublic !== undefined) formData.append('is_public', String(isPublic));
    const response = await httpClient.post<AssetAttachment>(`/assets/${id}/documents`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  generateReport: async (
    id: string,
    reportType: 'maintenance_summary' | 'incident_summary' | 'lifecycle_overview' | 'end_of_life_forecast' | 'custom',
    format: 'pdf' | 'excel',
    filters?: {
      date_from?: string;
      date_to?: string;
      severity?: string;
      cost_min?: number;
      cost_max?: number;
    }
  ): Promise<{ report_url: string; report_id: string }> => {
    const response = await httpClient.post<{ report_url: string; report_id: string }>(
      `/assets/${id}/reports`,
      {
        report_type: reportType,
        format,
        filters,
      }
    );
    return response.data;
  },
};
