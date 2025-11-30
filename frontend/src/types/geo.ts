export interface Coordinates {
  longitude: number;
  latitude: number;
}

export interface GeocodeResponse {
  coordinates: Coordinates;
  geojson: {
    type: 'Point';
    coordinates: [number, number];
  };
}

export interface ReverseGeocodeResponse {
  address: string;
  city: string;
  country: string;
}

export interface AddressSuggestion {
  address: string;
  coordinates: Coordinates;
  city?: string;
  country?: string;
}

export interface DistanceResponse {
  asset_id: string;
  distance_meters: number;
  distance_km: number;
}
