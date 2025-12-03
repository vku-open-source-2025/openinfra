import L from 'leaflet';
import ReactDOMServer from 'react-dom/server';
import { Zap, BatteryCharging, UtilityPole, TrafficCone, Lightbulb, Droplet, Waves, Activity } from 'lucide-react';
import React from 'react';

// Define a mapping from feature_code to Lucide icon and color
export const iconMapping: Record<string, { icon: React.ElementType, color: string, bgColor: string }> = {
    'tram_dien': { icon: Zap, color: '#fbbf24', bgColor: '#fef3c7' }, // Yellow
    'tram_sac': { icon: BatteryCharging, color: '#10b981', bgColor: '#d1fae5' }, // Green
    'cot_dien': { icon: UtilityPole, color: '#64748b', bgColor: '#f1f5f9' }, // Slate
    'den_giao_thong': { icon: TrafficCone, color: '#ef4444', bgColor: '#fee2e2' }, // Red
    'den_duong': { icon: Lightbulb, color: '#f97316', bgColor: '#fed7aa' }, // Orange
    'tru_chua_chay': { icon: Droplet, color: '#3b82f6', bgColor: '#dbeafe' }, // Blue
    'cong_thoat_nuoc': { icon: Waves, color: '#06b6d4', bgColor: '#cffafe' }, // Cyan
    'duong_ong_dien': { icon: Activity, color: '#8b5cf6', bgColor: '#e9d5ff' }, // Violet
};

export const getIconForAsset = (featureCode: string, isSelected: boolean = false) => {
    const config = iconMapping[featureCode] || { icon: Activity, color: '#94a3b8', bgColor: '#f1f5f9' };
    const IconComponent = config.icon;

    const size = isSelected ? 48 : 36;
    const iconSize = isSelected ? 24 : 20;
    const shadowSize = isSelected ? 12 : 8;

    // Render the icon component to get its SVG
    // Ensure the icon has proper attributes for rendering
    const iconSvg = ReactDOMServer.renderToStaticMarkup(
        React.createElement(IconComponent, {
            size: iconSize,
            strokeWidth: isSelected ? 2.5 : 2,
            color: 'currentColor',
            fill: 'none',
            stroke: 'currentColor',
            style: { display: 'block' }
        })
    );

    // Build the HTML string manually for better control
    const glowRing = isSelected
        ? `<div style="position: absolute; width: ${size + 8}px; height: ${size + 8}px; border-radius: 50%; background-color: ${config.color}; opacity: 0.2; animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;"></div>`
        : '';

    const iconHtml = `
        <div style="position: relative; width: ${size}px; height: ${size}px; display: flex; align-items: center; justify-content: center;">
            ${glowRing}
            <div style="position: relative; width: ${size}px; height: ${size}px; border-radius: 50%; background: ${isSelected
                ? `linear-gradient(135deg, ${config.bgColor} 0%, ${config.color}15 100%)`
                : `linear-gradient(135deg, ${config.color} 0%, ${config.color}dd 100%)`}; display: flex; align-items: center; justify-content: center; color: ${isSelected ? config.color : '#ffffff'}; box-shadow: ${isSelected
                ? `0 0 0 3px ${config.color}40, 0 4px 12px ${config.color}60, 0 8px 24px ${config.color}30`
                : `0 2px 8px rgba(0,0,0,0.15), 0 4px 12px rgba(0,0,0,0.1)`}; border: ${isSelected ? `3px solid ${config.color}` : `2.5px solid #ffffff`}; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); cursor: pointer; z-index: ${isSelected ? 10 : 1};">
                <div style="position: absolute; width: ${size * 0.7}px; height: ${size * 0.7}px; border-radius: 50%; background: rgba(255, 255, 255, 0.2); top: 15%; left: 15%;"></div>
                <div style="position: relative; z-index: 2; display: flex; align-items: center; justify-content: center; color: inherit; width: ${iconSize}px; height: ${iconSize}px;">
                    ${iconSvg}
                </div>
            </div>
            <div style="position: absolute; bottom: -${shadowSize}px; left: 50%; transform: translateX(-50%); width: ${size * 0.6}px; height: ${shadowSize}px; border-radius: 50%; background: rgba(0, 0, 0, 0.2); filter: blur(4px); z-index: 0;"></div>
        </div>
    `;

    return L.divIcon({
        html: iconHtml,
        className: 'custom-marker-icon',
        iconSize: [size, size],
        iconAnchor: [size / 2, size],
        popupAnchor: [0, -size],
    });
};

export const getColorForFeatureCode = (featureCode: string): string => {
    const config = iconMapping[featureCode];
    return config ? config.color : '#94a3b8'; // Default slate color
};
