import { httpClient } from '../lib/httpClient';
import type {
  Incident,
  IncidentCreateRequest,
  IncidentUpdateRequest,
  IncidentCommentRequest,
} from '../types/incident';
import { mockIncidents, delay } from './mocks/assetLifecycleMocks';

// Set to true to use mock data instead of real API calls
const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === 'true' || false;

export interface IncidentListParams {
  skip?: number;
  limit?: number;
  status?: string;
  severity?: string;
  asset_id?: string;
  assigned_to?: string;
  verification_status?: string;
}

export const incidentsApi = {
  list: async (params?: IncidentListParams): Promise<Incident[]> => {
    if (USE_MOCK_DATA && params?.asset_id) {
      await delay(400);
      let incidents = mockIncidents(params.asset_id);

      // Apply filters
      if (params.status) {
        incidents = incidents.filter(i => i.status === params.status);
      }
      if (params.severity) {
        incidents = incidents.filter(i => i.severity === params.severity);
      }

      return incidents;
    }
    const response = await httpClient.get<Incident[]>('/incidents', { params });
    return response.data;
  },

  getById: async (id: string): Promise<Incident> => {
    const response = await httpClient.get<Incident>(`/incidents/${id}`);
    return response.data;
  },

  create: async (data: IncidentCreateRequest): Promise<Incident> => {
    const response = await httpClient.post<Incident>('/incidents', data);
    return response.data;
  },

  update: async (id: string, data: IncidentUpdateRequest): Promise<Incident> => {
    const response = await httpClient.put<Incident>(`/incidents/${id}`, data);
    return response.data;
  },

  acknowledge: async (id: string): Promise<Incident> => {
    const response = await httpClient.post<Incident>(`/incidents/${id}/acknowledge`);
    return response.data;
  },

  assign: async (id: string, assignedTo: string): Promise<Incident> => {
    const response = await httpClient.post<Incident>(`/incidents/${id}/assign`, null, {
      params: { assigned_to: assignedTo },
    });
    return response.data;
  },

  resolve: async (
    id: string,
    resolutionNotes: string,
    resolutionType: 'fixed' | 'duplicate' | 'invalid' | 'deferred'
  ): Promise<Incident> => {
    const response = await httpClient.post<Incident>(`/incidents/${id}/resolve`, null, {
      params: {
        resolution_notes: resolutionNotes,
        resolution_type: resolutionType,
      },
    });
    return response.data;
  },

  addComment: async (id: string, data: IncidentCommentRequest): Promise<Incident> => {
    const response = await httpClient.post<Incident>(`/incidents/${id}/comments`, data);
    return response.data;
  },

  upvote: async (id: string): Promise<Incident> => {
    const response = await httpClient.post<Incident>(`/incidents/${id}/upvote`);
    return response.data;
  },

  createMaintenance: async (id: string): Promise<{ incident_id: string; maintenance_id: string; message: string }> => {
    const response = await httpClient.post<{ incident_id: string; maintenance_id: string; message: string }>(
      `/incidents/${id}/create-maintenance`
    );
    return response.data;
  },

  approveCost: async (id: string): Promise<Incident> => {
    const response = await httpClient.post<Incident>(`/incidents/${id}/approve-cost`);
    return response.data;
  },

  close: async (id: string, notes?: string): Promise<Incident> => {
    const response = await httpClient.post<Incident>(`/incidents/${id}/close`, null, {
      params: notes ? { notes } : undefined,
    });
    return response.data;
  },

  reject: async (id: string, reason: string): Promise<Incident> => {
    const response = await httpClient.post<Incident>(`/incidents/${id}/reject`, null, {
      params: { reason },
    });
    return response.data;
  },

  verify: async (id: string): Promise<Incident> => {
    const response = await httpClient.post<Incident>(`/incidents/${id}/verify`);
    return response.data;
  },
};
