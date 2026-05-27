import { httpClient } from '../lib/httpClient';
import { filterHazardsInLastHours } from '../lib/recentHazards';
import type { Hazard, HazardListParams, RecentHazardItem } from '../types/hazard';

export interface RecentHazardListParams extends HazardListParams {
  hours?: number;
}

export interface DeployHazardRequest {
  title?: string;
  additional_context?: string;
}

export interface DeployHazardResponse {
  hazard_id: string;
  event_id: string;
  eop_plan_id: string;
  markdown_body: string | null;
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

  /** Server-side recent hazards using /hazards/recent — returns RecentHazardItem[] */
  listRecentItems: async (params?: {
    hours?: number;
    limit?: number;
  }): Promise<RecentHazardItem[]> => {
    const response = await httpClient.get<RecentHazardItem[]>('/hazards/recent', {
      params: { hours: params?.hours ?? 24, limit: params?.limit ?? 200 },
    });
    return response.data;
  },

  /** Legacy client-side recent filter — returns Hazard[] (kept for PublicMap backward compat) */
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

  /** Deploy hazard → create EmergencyEvent + EOP draft.
   *  Returns hazard_id, event_id, eop_plan_id, markdown_body.
   *  Idempotent: returns existing linkage if hazard was already deployed.
   */
  deploy: async (
    hazardDbId: string,
    body?: DeployHazardRequest,
  ): Promise<DeployHazardResponse> => {
    const response = await httpClient.post<DeployHazardResponse>(
      `/hazards/${hazardDbId}/deploy`,
      body ?? {},
    );
    return response.data;
  },
};
