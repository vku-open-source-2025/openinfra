import { httpClient } from '../lib/httpClient';
import type { Incident, IncidentCreateRequest } from '../types/incident';

export interface PublicAssetInfo {
  asset_code: string;
  name: string;
  feature_type: string;
  category: string;
  status: 'active' | 'inactive' | 'maintenance' | 'decommissioned';
  location: {
    address: string;
    coordinates: {
      longitude: number;
      latitude: number;
    };
  };
  qr_code: string;
}

export interface AssetQRCodeResponse {
  asset_code: string;
  qr_code: string;
  url: string;
}

export const publicApi = {
  /**
   * Get public asset information by asset code
   * GET /public/assets/{code}
   */
  getPublicAsset: async (code: string): Promise<PublicAssetInfo> => {
    const response = await httpClient.get<PublicAssetInfo>(`/public/assets/${code}`);
    return response.data;
  },

  /**
   * Create an anonymous incident (no authentication required)
   * POST /public/incidents
   */
  createAnonymousIncident: async (data: IncidentCreateRequest): Promise<Incident> => {
    const response = await httpClient.post<Incident>('/public/incidents', data);
    return response.data;
  },

  /**
   * Get a public incident by ID (only if public_visible is true)
   * GET /public/incidents/{incident_id}
   */
  getPublicIncident: async (incidentId: string): Promise<Incident> => {
    const response = await httpClient.get<Incident>(`/public/incidents/${incidentId}`);
    return response.data;
  },

  /**
   * Get asset QR code
   * GET /public/assets/{code}/qr-code
   */
  getAssetQRCode: async (code: string): Promise<AssetQRCodeResponse> => {
    const response = await httpClient.get<AssetQRCodeResponse>(`/public/assets/${code}/qr-code`);
    return response.data;
  },

  /**
   * Upload photos for a public incident
   * POST /public/incidents/{incident_id}/photos
   */
  uploadPhotos: async (incidentId: string, files: File[]): Promise<Incident> => {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });

    const response = await httpClient.post<Incident>(
      `/public/incidents/${incidentId}/photos`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },
};
