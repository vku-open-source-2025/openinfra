import { useEffect, useRef } from 'react';
import L from 'leaflet';
import type { Hazard, HazardEventType, HazardSeverity } from '../types/hazard';

// ── Visual config ────────────────────────────────────────────────────────────

const SEVERITY_COLOR: Record<HazardSeverity, string> = {
  low: '#22c55e',
  medium: '#f59e0b',
  high: '#ef4444',
  critical: '#7c3aed',
};

const EVENT_EMOJI: Record<HazardEventType, string> = {
  flood: '🌊',
  storm: '🌪️',
  landslide: '⛰️',
  fire: '🔥',
  earthquake: '🌍',
  outage: '⚡',
  pollution: '☣️',
  drought: '🌵',
  traffic: '🚧',
  epidemic: '🦠',
  infrastructure_failure: '🏗️',
  other: '⚠️',
};

const EVENT_LABEL: Record<HazardEventType, string> = {
  flood: 'Lũ lụt',
  storm: 'Bão',
  landslide: 'Sạt lở',
  fire: 'Cháy rừng',
  earthquake: 'Động đất',
  outage: 'Mất điện',
  pollution: 'Ô nhiễm',
  drought: 'Hạn hán',
  traffic: 'Tắc nghẽn',
  epidemic: 'Dịch bệnh',
  infrastructure_failure: 'Sự cố hạ tầng',
  other: 'Khác',
};

const SEVERITY_LABEL: Record<HazardSeverity, string> = {
  low: 'Thấp',
  medium: 'Trung bình',
  high: 'Cao',
  critical: 'Nghiêm trọng',
};

// ── Helper ───────────────────────────────────────────────────────────────────

function makeHazardIcon(hazard: Hazard): L.DivIcon {
  const color = SEVERITY_COLOR[hazard.severity] ?? '#ef4444';
  const emoji = EVENT_EMOJI[hazard.event_type] ?? '⚠️';
  return L.divIcon({
    className: '',
    html: `
      <div style="
        position:relative;
        width:40px; height:40px;
        display:flex; align-items:center; justify-content:center;
      ">
        <!-- Pulsing ring for high/critical -->
        ${hazard.severity === 'high' || hazard.severity === 'critical' ? `
          <span style="
            position:absolute; inset:0; border-radius:50%;
            background:${color}33;
            animation: hazard-pulse 1.8s ease-out infinite;
          "></span>
        ` : ''}
        <div style="
          width:34px; height:34px; border-radius:50%;
          background:${color};
          border:3px solid white;
          box-shadow:0 2px 8px rgba(0,0,0,0.4);
          display:flex; align-items:center; justify-content:center;
          font-size:16px; line-height:1;
        ">${emoji}</div>
      </div>`,
    iconSize: [40, 40],
    iconAnchor: [20, 20],
    popupAnchor: [0, -22],
  });
}

function makePopupContent(h: Hazard): string {
  const color = SEVERITY_COLOR[h.severity] ?? '#ef4444';
  const emoji = EVENT_EMOJI[h.event_type] ?? '⚠️';
  const severityLabel = SEVERITY_LABEL[h.severity] ?? h.severity;
  const typeLabel = EVENT_LABEL[h.event_type] ?? h.event_type;
  const expiresAt = h.expires_at ? new Date(h.expires_at).toLocaleString('vi-VN') : 'Không xác định';
  return `
    <div style="min-width:200px; font-family:sans-serif">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
        <span style="font-size:20px">${emoji}</span>
        <div>
          <div style="font-weight:700;font-size:14px;color:#0f172a">${h.title}</div>
          <div style="font-size:11px;color:#64748b">${typeLabel}</div>
        </div>
      </div>
      <div style="display:inline-block;padding:2px 8px;border-radius:999px;background:${color}22;color:${color};font-size:11px;font-weight:700;margin-bottom:8px">
        ⚠ Mức độ: ${severityLabel}
      </div>
      ${h.description ? `<div style="font-size:12px;color:#374151;margin-bottom:6px">${h.description}</div>` : ''}
      ${h.district ? `<div style="font-size:11px;color:#64748b">📍 ${h.district}${h.ward ? ', ' + h.ward : ''}</div>` : ''}
      <div style="font-size:11px;color:#94a3b8;margin-top:4px">Hết hiệu lực: ${expiresAt}</div>
    </div>`;
}

// ── Component ────────────────────────────────────────────────────────────────

interface Props {
  map: L.Map;
  hazards: Hazard[];
  focusedHazardId?: string | null;
  focusNonce?: number;
}

const HazardMarkersLayer: React.FC<Props> = ({
  map,
  hazards,
  focusedHazardId,
  focusNonce,
}) => {
  const layerGroupRef = useRef<L.LayerGroup | null>(null);
  const markerByHazardIdRef = useRef<Map<string, L.Marker>>(new Map());

  // Inject pulse keyframe once
  useEffect(() => {
    const styleId = 'hazard-pulse-style';
    if (!document.getElementById(styleId)) {
      const style = document.createElement('style');
      style.id = styleId;
      style.textContent = `
        @keyframes hazard-pulse {
          0%   { transform:scale(1); opacity:.6; }
          70%  { transform:scale(2.2); opacity:0; }
          100% { transform:scale(1); opacity:0; }
        }`;
      document.head.appendChild(style);
    }
  }, []);

  useEffect(() => {
    if (!map) return;

    // Clean up previous layer group
    if (layerGroupRef.current) {
      map.removeLayer(layerGroupRef.current);
    }

    const group = L.layerGroup();
    const markerByHazardId = new Map<string, L.Marker>();

    hazards.forEach((h) => {
      if (!h.geometry?.coordinates) return;
      const geo = h.geometry;

      // Support Point geometry only for now (polygon/circle to be added later)
      if (geo.type === 'Point') {
        const [lng, lat] = geo.coordinates as number[];
        const marker = L.marker([lat, lng], { icon: makeHazardIcon(h) });
        marker.bindPopup(makePopupContent(h), { className: 'custom-popup', maxWidth: 260 });
        group.addLayer(marker);
        markerByHazardId.set(h.id, marker);
      }
    });

    group.addTo(map);
    layerGroupRef.current = group;
    markerByHazardIdRef.current = markerByHazardId;

    return () => {
      if (layerGroupRef.current) {
        map.removeLayer(layerGroupRef.current);
        layerGroupRef.current = null;
      }
      markerByHazardIdRef.current = new Map();
    };
  }, [map, hazards]);

  useEffect(() => {
    if (!focusedHazardId) {
      return;
    }

    const marker = markerByHazardIdRef.current.get(focusedHazardId);
    if (!marker) {
      return;
    }

    marker.openPopup();
  }, [focusedHazardId, focusNonce, hazards]);

  return null;
};

export default HazardMarkersLayer;
