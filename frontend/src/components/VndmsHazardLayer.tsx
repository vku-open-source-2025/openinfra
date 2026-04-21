import { useEffect, useRef } from 'react';
import L from 'leaflet';
import type { VndmsHazard } from '../hooks/useVndmsHazards';

// ── Types ────────────────────────────────────────────────────────────────────
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

function getRadius(h: VndmsHazard): number {
  if (h.warning_type === 'water_level') {
    if (h.warning_level === 1) return 8;
    if (h.warning_level === 2) return 12;
    return 16;
  }
  return h.severity === 'high' ? 12 : 8;
}

function buildPopup(h: VndmsHazard): string {
  return `
    <div style="font-size:13px;line-height:1.6;min-width:200px">
      <div style="font-weight:700;margin-bottom:4px">${h.label || '(Không có tên)'}</div>
      <div><b>Loại:</b> ${TYPE_LABEL_VI[h.warning_type] ?? h.warning_type}</div>
      ${h.value ? `<div><b>Giá trị:</b> ${h.value}</div>` : ''}
      <div><b>Mức độ:</b> ${SEVERITY_LABEL_VI[h.severity] ?? h.severity}</div>
      ${h.popupInfo ? `<div style="margin-top:4px;color:#555;font-size:11px">${h.popupInfo}</div>` : ''}
    </div>`;
}

// ── Layer component ──────────────────────────────────────────────────────────
interface Props {
  map: L.Map;
  hazards: VndmsHazard[];
}

const VndmsHazardLayer: React.FC<Props> = ({ map, hazards }) => {
  const layerRef = useRef<L.LayerGroup | null>(null);

  useEffect(() => {
    if (!map) return;

    if (layerRef.current) {
      map.removeLayer(layerRef.current);
    }

    const group = L.layerGroup();
    hazards.forEach((h) => {
      const color = TYPE_COLOR[h.warning_type] ?? '#94a3b8';
      L.circleMarker([h.lat, h.lon], {
        radius: getRadius(h),
        color,
        fillColor: color,
        fillOpacity: 0.7,
        weight: 1.5,
      })
        .bindPopup(buildPopup(h))
        .bindTooltip(h.label || h.warning_type, { direction: 'top', sticky: true })
        .addTo(group);
    });
    group.addTo(map);
    layerRef.current = group;

    return () => {
      if (layerRef.current) {
        map.removeLayer(layerRef.current);
        layerRef.current = null;
      }
    };
  }, [map, hazards]);

  return null;
};

export default VndmsHazardLayer;

// ── Legend (optional standalone component) ───────────────────────────────────
export const VndmsLegend: React.FC = () => (
  <div className="bg-white/95 border border-slate-200 rounded-lg shadow px-3 py-2 text-xs">
    <div className="font-bold text-slate-800 mb-1.5">Chú giải thiên tai</div>
    {[
      { color: TYPE_COLOR.water_level, label: 'Mực nước' },
      { color: TYPE_COLOR.warning_rain, label: 'Mưa' },
      { color: TYPE_COLOR.warning_wind, label: 'Gió' },
      { color: TYPE_COLOR.warning_flood, label: 'Lũ / Động đất' },
    ].map((it) => (
      <div key={it.label} className="flex items-center gap-1.5 mb-1">
        <span
          className="inline-block w-3 h-3 rounded-full border border-black/20"
          style={{ background: it.color }}
        />
        <span className="text-slate-600">{it.label}</span>
      </div>
    ))}
  </div>
);
