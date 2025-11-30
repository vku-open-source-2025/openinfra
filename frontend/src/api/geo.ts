import { httpClient } from '../lib/httpClient';
import type {
  Asset,
  GeocodeResponse,
  ReverseGeocodeResponse,
  AddressSuggestion,
  DistanceResponse,
  Coordinates,
} from '../types';

export interface NearbyAssetsParams {
  lng: number;
  lat: number;
  radius_meters?: number;
  feature_type?: string;
  limit?: number;
}

export interface WithinBoundsParams {
  min_lng: number;
  min_lat: number;
  max_lng: number;
  max_lat: number;
  feature_type?: string;
  limit?: number;
}

export interface WithinPolygonRequest {
  coordinates: number[][];
  feature_type?: string;
}

export interface GeocodeRequest {
  address: string;
  country?: string;
}

export interface ReverseGeocodeRequest {
  longitude: number;
  latitude: number;
}

export const geoApi = {
  findNearbyAssets: async (params: NearbyAssetsParams): Promise<Asset[]> => {
    const response = await httpClient.get<Asset[]>('/geo/assets/nearby', { params });
    return response.data;
  },

  findAssetsInBounds: async (params: WithinBoundsParams): Promise<Asset[]> => {
    const response = await httpClient.get<Asset[]>('/geo/assets/within-bounds', { params });
    return response.data;
  },

  findAssetsInPolygon: async (data: WithinPolygonRequest, limit?: number): Promise<Asset[]> => {
    const response = await httpClient.post<Asset[]>('/geo/assets/within-polygon', data, {
      params: limit ? { limit } : undefined,
    });
    return response.data;
  },

  geocode: async (data: GeocodeRequest): Promise<GeocodeResponse> => {
    const response = await httpClient.post<GeocodeResponse>('/geo/geocode', data);
    return response.data;
  },

  reverseGeocode: async (data: ReverseGeocodeRequest): Promise<ReverseGeocodeResponse> => {
    const response = await httpClient.post<ReverseGeocodeResponse>('/geo/reverse-geocode', data);
    return response.data;
  },

  searchAddress: async (q: string, limit?: number): Promise<AddressSuggestion[]> => {
    const response = await httpClient.get<AddressSuggestion[]>('/geo/search-address', {
      params: { q, limit },
    });
    return response.data;
  },

  calculateDistance: async (assetId: string, coordinates: Coordinates): Promise<DistanceResponse> => {
    const response = await httpClient.get<DistanceResponse>(`/geo/assets/${assetId}/distance-to`, {
      params: { lng: coordinates.longitude, lat: coordinates.latitude },
    });
    return response.data;
  },
};
