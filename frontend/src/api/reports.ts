import { httpClient } from '../lib/httpClient';
import type { Report, ReportCreateRequest } from '../types/report';

export interface ReportListParams {
  skip?: number;
  limit?: number;
  type?: string;
  status?: string;
}

export const reportsApi = {
  list: async (params?: ReportListParams): Promise<Report[]> => {
    const response = await httpClient.get<Report[]>('/reports', { params });
    return response.data;
  },

  getById: async (id: string): Promise<Report> => {
    const response = await httpClient.get<Report>(`/reports/${id}`);
    return response.data;
  },

  create: async (data: ReportCreateRequest): Promise<Report> => {
    const response = await httpClient.post<Report>('/reports', data);
    return response.data;
  },

  generate: async (id: string): Promise<Report> => {
    const response = await httpClient.post<Report>(`/reports/${id}/generate`);
    return response.data;
  },

  download: async (id: string): Promise<{ file_url: string; report_code: string; format: string }> => {
    const response = await httpClient.get<{ file_url: string; report_code: string; format: string }>(`/reports/${id}/download`);
    return response.data;
  },
};
