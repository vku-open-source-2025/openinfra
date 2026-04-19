import { httpClient } from '../lib/httpClient';
import type { Hazard, HazardListParams } from '../types/hazard';

export const hazardsApi = {
  list: async (params?: HazardListParams): Promise<Hazard[]> => {
    const { is_active, ...rest } = params ?? {};
    const queryParams = {
      ...rest,
      active_only: is_active,
    };

    const response = await httpClient.get<Hazard[]>('/hazards', { params: queryParams });
    return response.data;
  },

  nearby: async (params: {
    lat: number;
    lng: number;
    radius_m?: number;
    limit?: number;
  }): Promise<Hazard[]> => {
    const response = await httpClient.get<Hazard[]>('/hazards/geo/near', { params });
    return response.data;
  },

  expireStale: async (): Promise<{ updated: number }> => {
    const response = await httpClient.post<{ updated: number }>('/hazards/expire-stale');
    return response.data;
  },
};
