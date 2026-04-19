import { httpClient } from '../lib/httpClient';
import type {
  ResourceStatus,
  ResourceUnit,
  ResourceUnitCreateRequest,
  ResourceUnitUpdateRequest,
} from '../types/resource-unit';

export interface ResourceListParams {
  skip?: number;
  limit?: number;
  status?: string;
  resource_type?: string;
  district?: string;
}

export const resourcesApi = {
  list: async (params?: ResourceListParams): Promise<ResourceUnit[]> => {
    const response = await httpClient.get<ResourceUnit[]>('/emergency/resources', { params });
    return response.data;
  },

  getById: async (id: string): Promise<ResourceUnit> => {
    const response = await httpClient.get<ResourceUnit>(`/emergency/resources/${id}`);
    return response.data;
  },

  create: async (data: ResourceUnitCreateRequest): Promise<ResourceUnit> => {
    const response = await httpClient.post<ResourceUnit>('/emergency/resources', data);
    return response.data;
  },

  update: async (id: string, data: ResourceUnitUpdateRequest): Promise<ResourceUnit> => {
    const response = await httpClient.put<ResourceUnit>(`/emergency/resources/${id}`, data);
    return response.data;
  },

  setStatus: async (id: string, status: ResourceStatus): Promise<ResourceUnit> => {
    const response = await httpClient.post<ResourceUnit>(`/emergency/resources/${id}/status`, {
      status,
    });
    return response.data;
  },
};
