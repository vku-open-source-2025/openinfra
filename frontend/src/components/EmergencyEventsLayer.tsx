import { useEffect, useRef } from 'react';
import L from 'leaflet';
import type { PublicEmergencyEvent, EmergencySeverity, EmergencyEventType } from '../types/emergency';

const SEVERITY_COLOR: Record<EmergencySeverity, string> = {
  low: '#22c55e',
  medium: '#f59e0b',
  high: '#ef4444',
  critical: '#7c3aed',
};

const SEVERITY_LABEL: Record<EmergencySeverity, string> = {
  low: 'Thấp',
  medium: 'Trung bình',
  high: 'Cao',
  critical: 'Nghiêm trọng',
};

const TYPE_LABEL: Record<EmergencyEventType, string> = {
  flood: 'Lũ lụt',
  storm: 'Bão',
  landslide: 'Sạt lở',
  fire: 'Cháy rừng',
  earthquake: 'Động đất',
  outage: 'Mất điện',
  pollution: 'Ô nhiễm',
  other: 'Khác',
};

function makeEventIcon(event: PublicEmergencyEvent): L.DivIcon {
  const color = SEVERITY_COLOR[event.severity] ?? '#ef4444';
  const isHigh = event.severity === 'high' || event.severity === 'critical';
  return L.divIcon({
    className: '',
    html: `
      <div style="position:relative;width:46px;height:46px;display:flex;align-items:center;justify-content:center">
        ${
          isHigh
            ? `<span style="position:absolute;inset:0;border-radius:50%;background:${color}44;animation:event-pulse 1.6s ease-out infinite"></span>`
            : ''
        }
        <div style="
          width:38px;height:38px;border-radius:50%;
          background:${color};
          border:3px solid white;
          box-shadow:0 2px 10px rgba(0,0,0,0.45);
          display:flex;align-items:center;justify-content:center;
          font-size:20px;line-height:1;
        ">🚨</div>
      </div>`,
    iconSize: [46, 46],
    iconAnchor: [23, 23],
    popupAnchor: [0, -24],
  });
}

function locationText(e: PublicEmergencyEvent): string {
  const loc = e.location;
  if (!loc) return '';
  const parts = [loc.address, loc.ward, loc.district, loc.city].filter(Boolean);
  return parts.join(', ');
}

function makePopupContent(e: PublicEmergencyEvent): string {
  const color = SEVERITY_COLOR[e.severity] ?? '#ef4444';
  const severityLabel = SEVERITY_LABEL[e.severity] ?? e.severity;
  const typeLabel = TYPE_LABEL[e.event_type] ?? e.event_type;
  const startedAt = e.started_at ? new Date(e.started_at).toLocaleString('vi-VN') : '';
  const loc = locationText(e);
  return `
    <div style="min-width:220px;font-family:sans-serif">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
        <span style="font-size:20px">🚨</span>
        <div>
          <div style="font-weight:700;font-size:14px;color:#0f172a">${e.title}</div>
          <div style="font-size:11px;color:#64748b">${typeLabel} · Đang triển khai cứu hộ</div>
        </div>
      </div>
      <div style="display:inline-block;padding:2px 8px;border-radius:999px;background:${color}22;color:${color};font-size:11px;font-weight:700;margin-bottom:8px">
        ⚠ Mức độ: ${severityLabel}
      </div>
      ${loc ? `<div style="font-size:11px;color:#64748b;margin-top:4px">📍 ${loc}</div>` : ''}
      ${startedAt ? `<div style="font-size:11px;color:#94a3b8;margin-top:4px">Bắt đầu: ${startedAt}</div>` : ''}
    </div>`;
}

interface Props {
  map: L.Map;
  events: PublicEmergencyEvent[];
  focusedEventId?: string | null;
  focusNonce?: number;
}

const EmergencyEventsLayer: React.FC<Props> = ({ map, events, focusedEventId, focusNonce }) => {
  const layerGroupRef = useRef<L.LayerGroup | null>(null);
  const markerByEventIdRef = useRef<Map<string, L.Marker>>(new Map());

  useEffect(() => {
    const styleId = 'event-pulse-style';
    if (!document.getElementById(styleId)) {
      const style = document.createElement('style');
      style.id = styleId;
      style.textContent = `
        @keyframes event-pulse {
          0%   { transform:scale(1); opacity:.7; }
          70%  { transform:scale(2.4); opacity:0; }
          100% { transform:scale(1); opacity:0; }
        }`;
      document.head.appendChild(style);
    }
  }, []);

  useEffect(() => {
    if (!map) return;

    if (layerGroupRef.current) {
      map.removeLayer(layerGroupRef.current);
    }

    const group = L.layerGroup();
    const markerByEventId = new Map<string, L.Marker>();

    events.forEach((e) => {
      if (!e.geometry?.coordinates) return;
      if (e.geometry.type === 'Point') {
        const [lng, lat] = e.geometry.coordinates as number[];
        if (typeof lat !== 'number' || typeof lng !== 'number') return;
        const marker = L.marker([lat, lng], { icon: makeEventIcon(e) });
        marker.bindPopup(makePopupContent(e), { className: 'custom-popup', maxWidth: 280 });
        group.addLayer(marker);
        markerByEventId.set(e.id, marker);
      }
    });

    group.addTo(map);
    layerGroupRef.current = group;
    markerByEventIdRef.current = markerByEventId;

    return () => {
      if (layerGroupRef.current) {
        map.removeLayer(layerGroupRef.current);
        layerGroupRef.current = null;
      }
      markerByEventIdRef.current = new Map();
    };
  }, [map, events]);

  useEffect(() => {
    if (!focusedEventId) return;
    const marker = markerByEventIdRef.current.get(focusedEventId);
    if (!marker) return;
    marker.openPopup();
  }, [focusedEventId, focusNonce, events]);

  return null;
};

export default EmergencyEventsLayer;
