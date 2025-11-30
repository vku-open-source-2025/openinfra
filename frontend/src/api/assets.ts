import { httpClient } from '../lib/httpClient';
import type { Asset, AssetCreateRequest, AssetUpdateRequest } from '../types/asset';

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
};
