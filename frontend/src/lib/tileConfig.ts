/**
 * Shared tile configuration helper.
 * Fetches tile URL from the backend (which hides the API key server-side).
 * Falls back to OpenStreetMap if the backend is unreachable or has no key configured.
 */

const BASE_API: string = import.meta.env.VITE_BASE_API_URL ?? "";

export interface TileConfig {
  tileUrl: string;
  attribution: string;
  maxZoom: number;
  maxNativeZoom?: number;
  provider: string;
}

let _cachedTileConfig: TileConfig | null = null;

export async function fetchTileConfig(): Promise<TileConfig> {
  if (_cachedTileConfig) return _cachedTileConfig;
  try {
    const res = await fetch(`${BASE_API}/map/config`);
    const cfg: TileConfig = await res.json();
    // If tileUrl is relative, prepend the API origin so Leaflet resolves correctly
    if (cfg.tileUrl && !cfg.tileUrl.startsWith("http")) {
      const apiOrigin = BASE_API.replace(/\/api\/v1$/, "");
      cfg.tileUrl = `${apiOrigin}${cfg.tileUrl}`;
    }
    _cachedTileConfig = cfg;
  } catch {
    _cachedTileConfig = {
      tileUrl: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      attribution:
        '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 20,
      maxNativeZoom: 16,
      provider: "osm",
    };
  }
  return _cachedTileConfig!;
}
