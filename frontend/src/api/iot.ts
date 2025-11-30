import { httpClient } from '../lib/httpClient';
import type {
  IoTSensor,
  SensorReading,
  SensorStatistics,
  SensorCreateRequest,
  SensorUpdateRequest,
  SensorReadingIngestRequest,
} from '../types/iot';

export interface SensorListParams {
  skip?: number;
  limit?: number;
  asset_id?: string;
  sensor_type?: string;
  status?: string;
}

export interface SensorDataParams {
  from_time: string;
  to_time: string;
  limit?: number;
}

export interface SensorStatisticsParams {
  from_time: string;
  to_time: string;
  granularity?: 'minute' | 'hour' | 'day';
}

export const iotApi = {
  listSensors: async (params?: SensorListParams): Promise<IoTSensor[]> => {
    const response = await httpClient.get<IoTSensor[]>('/iot/sensors', { params });
    return response.data;
  },

  getSensorById: async (id: string): Promise<IoTSensor> => {
    const response = await httpClient.get<IoTSensor>(`/iot/sensors/${id}`);
    return response.data;
  },

  createSensor: async (data: SensorCreateRequest): Promise<IoTSensor> => {
    const response = await httpClient.post<IoTSensor>('/iot/sensors', data);
    return response.data;
  },

  updateSensor: async (id: string, data: SensorUpdateRequest): Promise<IoTSensor> => {
    const response = await httpClient.put<IoTSensor>(`/iot/sensors/${id}`, data);
    return response.data;
  },

  deleteSensor: async (id: string): Promise<void> => {
    await httpClient.delete(`/iot/sensors/${id}`);
  },

  getSensorData: async (id: string, params: SensorDataParams): Promise<SensorReading[]> => {
    const response = await httpClient.get<SensorReading[]>(`/iot/sensors/${id}/data`, { params });
    return response.data;
  },

  ingestReading: async (id: string, data: SensorReadingIngestRequest): Promise<SensorReading> => {
    const response = await httpClient.post<SensorReading>(`/iot/sensors/${id}/data`, data);
    return response.data;
  },

  batchIngest: async (readings: Array<{ sensor_id: string } & SensorReadingIngestRequest>): Promise<{ ingested: number; failed: number }> => {
    const response = await httpClient.post<{ ingested: number; failed: number }>('/iot/sensors/batch-ingest', { readings });
    return response.data;
  },

  getSensorStatus: async (id: string): Promise<{ sensor_id: string; status: string; last_seen?: string; last_reading?: number }> => {
    const response = await httpClient.get(`/iot/sensors/${id}/status`);
    return response.data;
  },

  getSensorStatistics: async (id: string, params: SensorStatisticsParams): Promise<SensorStatistics> => {
    const response = await httpClient.get<SensorStatistics>(`/iot/sensors/${id}/statistics`, { params });
    return response.data;
  },
};
