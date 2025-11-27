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

export const getIconForAsset = (featureCode: string, isSelected: boolean = false) => {
    const config = iconMapping[featureCode] || { icon: Activity, color: '#94a3b8' };
    const IconComponent = config.icon;

    const iconHtml = ReactDOMServer.renderToString(
        <div style={{
            backgroundColor: isSelected ? '#ffffff' : config.color, // White background if selected
            width: isSelected ? '40px' : '32px', // Larger if selected
            height: isSelected ? '40px' : '32px',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: isSelected ? config.color : 'white', // Colored icon if selected
            boxShadow: isSelected ? `0 0 15px ${config.color}, 0 0 5px ${config.color}` : '0 2px 5px rgba(0,0,0,0.2)', // Glow effect
            border: isSelected ? `3px solid ${config.color}` : '2px solid white',
            transition: 'all 0.3s ease'
        }}>
            <IconComponent size={isSelected ? 24 : 18} />
        </div>
    );

    return L.divIcon({
        html: iconHtml,
        className: 'custom-marker-icon',
        iconSize: isSelected ? [40, 40] : [32, 32],
        iconAnchor: isSelected ? [20, 40] : [16, 32],
        popupAnchor: [0, isSelected ? -40 : -32]
    });
};

export const getColorForFeatureCode = (featureCode: string): string => {
    const config = iconMapping[featureCode];
    return config ? config.color : '#94a3b8'; // Default slate color
};
