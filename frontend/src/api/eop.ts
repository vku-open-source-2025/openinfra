import { httpClient } from '../lib/httpClient';
import type {
  EOPGenerateRequest,
  EOPPlan,
  EOPPlanCreateRequest,
  EOPPlanUpdateRequest,
} from '../types/eop';

export interface EOPListParams {
  skip?: number;
  limit?: number;
  emergency_event_id?: string;
  status?: string;
}

export const eopApi = {
  list: async (params?: EOPListParams): Promise<EOPPlan[]> => {
    const response = await httpClient.get<EOPPlan[]>('/emergency/eop', { params });
    return response.data;
  },

  getById: async (id: string): Promise<EOPPlan> => {
    const response = await httpClient.get<EOPPlan>(`/emergency/eop/${id}`);
    return response.data;
  },

  create: async (data: EOPPlanCreateRequest): Promise<EOPPlan> => {
    const response = await httpClient.post<EOPPlan>('/emergency/eop', data);
    return response.data;
  },

  update: async (id: string, data: EOPPlanUpdateRequest): Promise<EOPPlan> => {
    const response = await httpClient.put<EOPPlan>(`/emergency/eop/${id}`, data);
    return response.data;
  },

  approve: async (id: string, reviewNotes?: string): Promise<EOPPlan> => {
    const response = await httpClient.post<EOPPlan>(`/emergency/eop/${id}/approve`, {
      review_notes: reviewNotes,
    });
    return response.data;
  },

  publish: async (id: string): Promise<EOPPlan> => {
    const response = await httpClient.post<EOPPlan>(`/emergency/eop/${id}/publish`);
    return response.data;
  },

  generateDraft: async (payload: EOPGenerateRequest): Promise<EOPPlan> => {
    const response = await httpClient.post<EOPPlan>('/emergency/eop/generate-draft', payload);
    return response.data;
  },
};
