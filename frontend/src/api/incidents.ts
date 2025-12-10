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

  createMaintenance: async (id: string, technicianId?: string): Promise<{ incident_id: string; maintenance_id: string; message: string }> => {
    const response = await httpClient.post<{ incident_id: string; maintenance_id: string; message: string }>(
      `/incidents/${id}/create-maintenance`,
      null,
      {
        params: technicianId ? { technician_id: technicianId } : undefined,
      }
    );
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

  checkDuplicates: async (id: string): Promise<Array<{ incident_id: string; similarity_score: number; match_reasons: string[] }>> => {
    const response = await httpClient.post<Array<{ incident_id: string; similarity_score: number; match_reasons: string[] }>>(
      `/incidents/${id}/check-duplicates`
    );
    return response.data;
  },

  getMergeSuggestions: async (id: string, status?: string): Promise<Array<any>> => {
    const response = await httpClient.get<Array<any>>(`/incidents/${id}/merge-suggestions`, {
      params: status ? { status } : undefined,
    });
    return response.data;
  },

  mergeIncidents: async (
    id: string,
    duplicateIds: string[],
    mergeNotes?: string
  ): Promise<Incident> => {
    const response = await httpClient.post<Incident>(`/incidents/${id}/merge`, {
      duplicate_ids: duplicateIds,
      merge_notes: mergeNotes,
    });
    return response.data;
  },

  approveMergeSuggestion: async (suggestionId: string): Promise<Incident> => {
    const response = await httpClient.post<Incident>(
      `/incidents/merge-suggestions/${suggestionId}/approve`
    );
    return response.data;
  },

  rejectMergeSuggestion: async (suggestionId: string, reviewNotes?: string): Promise<{ message: string }> => {
    const response = await httpClient.post<{ message: string }>(
      `/incidents/merge-suggestions/${suggestionId}/reject`,
      reviewNotes ? { review_notes: reviewNotes } : undefined
    );
    return response.data;
  },

  getRelatedIncidents: async (id: string): Promise<Incident[]> => {
    const response = await httpClient.get<Incident[]>(`/incidents/${id}/related`);
    return response.data;
  },
};
