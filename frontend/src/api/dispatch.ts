import { httpClient } from '../lib/httpClient';
import type {
  DispatchOptimizeRequest,
  DispatchOptimizeResult,
  DispatchOrder,
  DispatchOrderCreateRequest,
  DispatchOrderUpdateRequest,
} from '../types/dispatch';

export interface DispatchListParams {
  skip?: number;
  limit?: number;
  emergency_event_id?: string;
  status?: string;
  priority?: string;
}

export const dispatchApi = {
  list: async (params?: DispatchListParams): Promise<DispatchOrder[]> => {
    const response = await httpClient.get<DispatchOrder[]>('/emergency/dispatch', { params });
    return response.data;
  },

  getById: async (id: string): Promise<DispatchOrder> => {
    const response = await httpClient.get<DispatchOrder>(`/emergency/dispatch/${id}`);
    return response.data;
  },

  create: async (data: DispatchOrderCreateRequest): Promise<DispatchOrder> => {
    const response = await httpClient.post<DispatchOrder>('/emergency/dispatch', data);
    return response.data;
  },

  update: async (id: string, data: DispatchOrderUpdateRequest): Promise<DispatchOrder> => {
    const response = await httpClient.put<DispatchOrder>(`/emergency/dispatch/${id}`, data);
    return response.data;
  },

  assign: async (id: string): Promise<DispatchOrder> => {
    const response = await httpClient.post<DispatchOrder>(`/emergency/dispatch/${id}/assign`);
    return response.data;
  },

  complete: async (id: string): Promise<DispatchOrder> => {
    const response = await httpClient.post<DispatchOrder>(`/emergency/dispatch/${id}/complete`);
    return response.data;
  },

  optimize: async (payload: DispatchOptimizeRequest = {}): Promise<DispatchOptimizeResult> => {
    const response = await httpClient.post<DispatchOptimizeResult>('/emergency/dispatch/optimize', payload);
    return response.data;
  },
};
