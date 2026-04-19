import { httpClient } from '../lib/httpClient';
import type {
  Sitrep,
  SitrepCreateRequest,
  SitrepDelta,
  SitrepUpdateRequest,
} from '../types/sitrep';

export interface SitrepListParams {
  skip?: number;
  limit?: number;
  emergency_event_id?: string;
  status?: string;
}

export const sitrepApi = {
  list: async (params?: SitrepListParams): Promise<Sitrep[]> => {
    const response = await httpClient.get<Sitrep[]>('/emergency/sitrep', { params });
    return response.data;
  },

  getById: async (id: string): Promise<Sitrep> => {
    const response = await httpClient.get<Sitrep>(`/emergency/sitrep/${id}`);
    return response.data;
  },

  create: async (data: SitrepCreateRequest): Promise<Sitrep> => {
    const response = await httpClient.post<Sitrep>('/emergency/sitrep', data);
    return response.data;
  },

  update: async (id: string, data: SitrepUpdateRequest): Promise<Sitrep> => {
    const response = await httpClient.put<Sitrep>(`/emergency/sitrep/${id}`, data);
    return response.data;
  },

  appendDelta: async (id: string, data: SitrepDelta): Promise<Sitrep> => {
    const response = await httpClient.post<Sitrep>(`/emergency/sitrep/${id}/delta`, data);
    return response.data;
  },

  publish: async (id: string): Promise<Sitrep> => {
    const response = await httpClient.post<Sitrep>(`/emergency/sitrep/${id}/publish`);
    return response.data;
  },
};
