import { httpClient } from '../lib/httpClient';
import { filterHazardsInLastHours } from '../lib/recentHazards';
import type { Hazard, HazardListParams } from '../types/hazard';

export interface RecentHazardListParams extends HazardListParams {
  hours?: number;
}

async function listHazards(params?: HazardListParams): Promise<Hazard[]> {
  const { is_active, ...rest } = params ?? {};
  const queryParams = {
    ...rest,
    active_only: is_active,
  };

  const response = await httpClient.get<Hazard[]>('/hazards', { params: queryParams });
  return response.data;
}

export const hazardsApi = {
  list: listHazards,

  listRecent: async (params?: RecentHazardListParams): Promise<Hazard[]> => {
    const { hours = 24, ...listParams } = params ?? {};
    const hazards = await listHazards({
      is_active: true,
      limit: 200,
      ...listParams,
    });
    return filterHazardsInLastHours(hazards, hours);
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
