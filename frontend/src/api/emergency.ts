import { httpClient } from '../lib/httpClient';
import type {
  EmergencyEvent,
  EmergencyEventCreateRequest,
  EmergencyEventUpdateRequest,
} from '../types/emergency';

export interface EmergencyListParams {
  skip?: number;
  limit?: number;
  status?: string;
  severity?: string;
  event_type?: string;
  q?: string;
}

export interface SosconnStatusResponse {
  provider: string;
  configured: boolean;
  reachable: boolean;
  model?: string | null;
  detail?: string | null;
  checked_at: string;
  base_url: string;
}

export interface SosTimelineItem {
  event_id: string;
  event_code?: string | null;
  title: string;
  severity: string;
  status: string;
  created_at: string;
  source_ref?: string | null;
  sla_breach_count: number;
  last_update: string;
}

export const emergencyApi = {
  list: async (params?: EmergencyListParams): Promise<EmergencyEvent[]> => {
    const response = await httpClient.get<EmergencyEvent[]>('/emergency', { params });
    return response.data;
  },

  getById: async (id: string): Promise<EmergencyEvent> => {
    const response = await httpClient.get<EmergencyEvent>(`/emergency/${id}`);
    return response.data;
  },

  create: async (data: EmergencyEventCreateRequest): Promise<EmergencyEvent> => {
    const response = await httpClient.post<EmergencyEvent>('/emergency', data);
    return response.data;
  },

  update: async (id: string, data: EmergencyEventUpdateRequest): Promise<EmergencyEvent> => {
    const response = await httpClient.put<EmergencyEvent>(`/emergency/${id}`, data);
    return response.data;
  },

  resolve: async (id: string, resolutionNote?: string): Promise<EmergencyEvent> => {
    const response = await httpClient.post<EmergencyEvent>(`/emergency/${id}/resolve`, {
      resolution_note: resolutionNote,
    });
    return response.data;
  },

  getSosconnStatus: async (): Promise<SosconnStatusResponse> => {
    const response = await httpClient.get<SosconnStatusResponse>('/emergency/sosconn/status');
    return response.data;
  },

  getSosTimeline: async (params?: { limit?: number }): Promise<SosTimelineItem[]> => {
    const response = await httpClient.get<SosTimelineItem[]>('/emergency/sos/timeline', {
      params,
    });
    return response.data;
  },
};
