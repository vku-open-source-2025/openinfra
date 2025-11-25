import L from 'leaflet';
import ReactDOMServer from 'react-dom/server';
import { Zap, BatteryCharging, UtilityPole, TrafficCone, Lightbulb, Droplet, Waves, Activity } from 'lucide-react';
import React from 'react';

// Define a mapping from feature_code to Lucide icon and color
const iconMapping: Record<string, { icon: React.ElementType, color: string }> = {
    'tram_dien': { icon: Zap, color: '#eab308' }, // Yellow
    'tram_sac': { icon: BatteryCharging, color: '#22c55e' }, // Green
    'cot_dien': { icon: UtilityPole, color: '#64748b' }, // Slate
    'den_giao_thong': { icon: TrafficCone, color: '#ef4444' }, // Red
    'den_duong': { icon: Lightbulb, color: '#f97316' }, // Orange
    'tru_chua_chay': { icon: Droplet, color: '#3b82f6' }, // Blue
    'cong_thoat_nuoc': { icon: Waves, color: '#06b6d4' }, // Cyan
    'duong_ong_dien': { icon: Activity, color: '#8b5cf6' }, // Violet
};

export const getIconForAsset = (featureCode: string) => {
    const config = iconMapping[featureCode] || { icon: Activity, color: '#94a3b8' };
    const IconComponent = config.icon;

    const iconHtml = ReactDOMServer.renderToString(
        <div style={{
            backgroundColor: config.color,
            width: '32px',
            height: '32px',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            boxShadow: '0 2px 5px rgba(0,0,0,0.2)',
            border: '2px solid white'
        }}>
            <IconComponent size={18} />
        </div>
    );

    return L.divIcon({
        html: iconHtml,
        className: 'custom-marker-icon',
        iconSize: [32, 32],
        iconAnchor: [16, 32],
        popupAnchor: [0, -32]
    });
};
