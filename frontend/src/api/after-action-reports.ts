import { httpClient } from '../lib/httpClient';
import type {
  AfterActionGenerateRequest,
  AfterActionReport,
  AfterActionUpdateRequest,
} from '../types/after-action-report';

export interface AfterActionListParams {
  skip?: number;
  limit?: number;
  event_id?: string;
  status?: string;
}

export const afterActionApi = {
  list: async (params?: AfterActionListParams): Promise<AfterActionReport[]> => {
    const response = await httpClient.get<AfterActionReport[]>('/emergency/after-action', { params });
    return response.data;
  },

  getById: async (id: string): Promise<AfterActionReport> => {
    const response = await httpClient.get<AfterActionReport>(`/emergency/after-action/${id}`);
    return response.data;
  },

  generate: async (payload: AfterActionGenerateRequest): Promise<AfterActionReport> => {
    const response = await httpClient.post<AfterActionReport>(
      '/emergency/after-action/generate',
      payload
    );
    return response.data;
  },

  update: async (id: string, payload: AfterActionUpdateRequest): Promise<AfterActionReport> => {
    const response = await httpClient.put<AfterActionReport>(`/emergency/after-action/${id}`, payload);
    return response.data;
  },

  publish: async (id: string): Promise<AfterActionReport> => {
    const response = await httpClient.post<AfterActionReport>(`/emergency/after-action/${id}/publish`);
    return response.data;
  },
};
