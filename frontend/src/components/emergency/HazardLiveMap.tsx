import React from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { httpClient } from '@/lib/httpClient';
import { fetchTileConfig } from '@/lib/tileConfig';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface VndmsHazard {
  id: string;
  lat: number;
  lon: number;
  label: string;
  warning_type: 'water_level' | 'warning_rain' | 'warning_wind' | 'warning_earthquake' | 'warning_flood';
  warning_level: number;
  severity: 'low' | 'medium' | 'high';
  value: string;
  popupInfo: string;
  source: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const TYPE_COLOR: Record<string, string> = {
  water_level: '#3b82f6',
  warning_rain: '#10b981',
  warning_wind: '#f59e0b',
  warning_earthquake: '#ef4444',
  warning_flood: '#ef4444',
};

const TYPE_LABEL_VI: Record<string, string> = {
  water_level: 'Mực nước',
  warning_rain: 'Cảnh báo mưa',
  warning_wind: 'Cảnh báo gió',
  warning_earthquake: 'Động đất',
  warning_flood: 'Lũ lụt',
};

const SEVERITY_LABEL_VI: Record<string, string> = {
  low: 'Thấp',
  medium: 'Trung bình',
  high: 'Cao',
};

function getRadius(hazard: VndmsHazard): number {
  if (hazard.warning_type === 'water_level') {
    if (hazard.warning_level === 1) return 8;
    if (hazard.warning_level === 2) return 12;
    return 16;
  }
  return hazard.severity === 'high' ? 12 : 8;
}

function buildPopupHtml(h: VndmsHazard): string {
  return `
    <div style="font-size:13px;line-height:1.6;min-width:200px">
      <div style="font-weight:700;margin-bottom:4px">${h.label || '(Không có tên)'}</div>
      <div><b>Loại:</b> ${TYPE_LABEL_VI[h.warning_type] ?? h.warning_type}</div>
      ${h.value ? `<div><b>Giá trị:</b> ${h.value}</div>` : ''}
      <div><b>Mức độ:</b> ${SEVERITY_LABEL_VI[h.severity] ?? h.severity}</div>
      ${h.popupInfo ? `<div style="margin-top:4px;color:#555;font-size:11px">${h.popupInfo}</div>` : ''}
    </div>
  `;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
const VIETNAM_CENTER: [number, number] = [16.0, 107.0];
const DEFAULT_ZOOM = 5;
const REFRESH_INTERVAL_MS = 60_000;

// Accept (and ignore) any legacy `hazards` prop so callers don't break
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const HazardLiveMap: React.FC<{ hazards?: any[] }> = () => {
  const containerRef = React.useRef<HTMLDivElement | null>(null);
  const mapRef = React.useRef<L.Map | null>(null);
  const markerLayerRef = React.useRef<L.LayerGroup | null>(null);

  const [hazards, setHazards] = React.useState<VndmsHazard[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = React.useState<Date | null>(null);

  // ---- Fetch ---
  const fetchHazards = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await httpClient.get<VndmsHazard[]>('/hazards/vndms-live');
      setHazards(resp.data ?? []);
      setLastUpdated(new Date());
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Không thể tải dữ liệu';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial fetch + interval
  React.useEffect(() => {
    fetchHazards();
    const timer = setInterval(fetchHazards, REFRESH_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [fetchHazards]);

  // ---- Init map once ---
  React.useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = L.map(containerRef.current, {
      center: VIETNAM_CENTER,
      zoom: DEFAULT_ZOOM,
      maxZoom: 19,
      scrollWheelZoom: true,
    });

    // Use VietMap tiles (falls back to OSM if not configured)
    fetchTileConfig().then((cfg) => {
      if (!mapRef.current) return;
      L.tileLayer(cfg.tileUrl, {
        attribution: cfg.attribution,
        maxZoom: cfg.maxZoom,
        ...(cfg.maxNativeZoom ? { maxNativeZoom: cfg.maxNativeZoom } : {}),
      }).addTo(mapRef.current);
    });

    markerLayerRef.current = L.layerGroup().addTo(map);
    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
      markerLayerRef.current = null;
    };
  }, []);

  // ---- Update markers when hazards change ---
  React.useEffect(() => {
    if (!mapRef.current || !markerLayerRef.current) return;
    const markerLayer = markerLayerRef.current;
    markerLayer.clearLayers();

    hazards.forEach((h) => {
      const color = TYPE_COLOR[h.warning_type] ?? '#94a3b8';
      const radius = getRadius(h);
      L.circleMarker([h.lat, h.lon], {
        radius,
        color,
        fillColor: color,
        fillOpacity: 0.75,
        weight: 1.5,
      })
        .bindPopup(buildPopupHtml(h))
        .bindTooltip(h.label || h.warning_type, { direction: 'top', sticky: true })
        .addTo(markerLayer);
    });
  }, [hazards]);

  // ---- Legend HTML ---
  const legendItems = [
    { color: TYPE_COLOR.water_level, label: 'Mực nước' },
    { color: TYPE_COLOR.warning_rain, label: 'Mưa' },
    { color: TYPE_COLOR.warning_wind, label: 'Gió' },
    { color: TYPE_COLOR.warning_flood, label: 'Lũ / Động đất' },
  ];

  return (
    <div style={{ position: 'relative', width: '100%', height: '400px' }}>
      {/* Map container */}
      <div ref={containerRef} style={{ width: '100%', height: '100%', borderRadius: '8px', border: '1px solid #e2e8f0' }} />

      {/* Loading overlay */}
      {loading && (
        <div
          style={{
            position: 'absolute', inset: 0, display: 'flex', alignItems: 'center',
            justifyContent: 'center', background: 'rgba(255,255,255,0.7)',
            borderRadius: '8px', zIndex: 1000,
          }}
        >
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
            <div
              style={{
                width: 32, height: 32, border: '3px solid #e2e8f0',
                borderTopColor: '#3b82f6', borderRadius: '50%',
                animation: 'spin 0.8s linear infinite',
              }}
            />
            <span style={{ fontSize: 13, color: '#64748b' }}>Đang tải dữ liệu VNDMS…</span>
          </div>
        </div>
      )}

      {/* Error banner */}
      {error && !loading && (
        <div
          style={{
            position: 'absolute', top: 8, left: 8, right: 8, zIndex: 1000,
            background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: 6,
            padding: '6px 12px', fontSize: 12, color: '#b91c1c',
          }}
        >
          ⚠️ {error}
        </div>
      )}

      {/* Refresh button */}
      <button
        onClick={fetchHazards}
        disabled={loading}
        style={{
          position: 'absolute', top: 8, right: 8, zIndex: 1000,
          background: '#fff', border: '1px solid #cbd5e1', borderRadius: 6,
          padding: '4px 10px', fontSize: 12, cursor: loading ? 'not-allowed' : 'pointer',
          display: 'flex', alignItems: 'center', gap: 4, color: '#334155',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        }}
      >
        <span style={{ fontSize: 14 }}>↻</span> Làm mới
      </button>

      {/* Last updated */}
      {lastUpdated && !loading && (
        <div
          style={{
            position: 'absolute', top: 8, left: 8, zIndex: 1000,
            background: 'rgba(255,255,255,0.9)', border: '1px solid #e2e8f0',
            borderRadius: 6, padding: '3px 8px', fontSize: 11, color: '#64748b',
          }}
        >
          Cập nhật: {lastUpdated.toLocaleTimeString('vi-VN')} · {hazards.length} điểm
        </div>
      )}

      {/* Legend */}
      <div
        style={{
          position: 'absolute', bottom: 24, left: 8, zIndex: 1000,
          background: 'rgba(255,255,255,0.95)', border: '1px solid #e2e8f0',
          borderRadius: 8, padding: '8px 12px', fontSize: 11,
          boxShadow: '0 1px 4px rgba(0,0,0,0.12)',
          minWidth: 130,
        }}
      >
        <div style={{ fontWeight: 700, marginBottom: 6, color: '#1e293b', fontSize: 12 }}>Chú giải</div>
        {legendItems.map((item) => (
          <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
            <span
              style={{
                display: 'inline-block', width: 12, height: 12,
                borderRadius: '50%', background: item.color,
                border: '1px solid rgba(0,0,0,0.2)', flexShrink: 0,
              }}
            />
            <span style={{ color: '#475569' }}>{item.label}</span>
          </div>
        ))}
      </div>

      {/* Spin animation */}
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
};

export default HazardLiveMap;
