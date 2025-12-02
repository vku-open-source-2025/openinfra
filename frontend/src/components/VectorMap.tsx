import { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

interface VectorMapProps {
    center?: [number, number];
    zoom?: number;
    className?: string;
}

// Vietnam sovereignty markers
const VIETNAM_ISLANDS = [
    {
        name: 'Quần đảo Hoàng Sa',
        nameEn: 'Paracel Islands',
        coordinates: [112.0, 16.5] as [number, number],
    },
    {
        name: 'Quần đảo Trường Sa',
        nameEn: 'Spratly Islands',
        coordinates: [114.0, 10.0] as [number, number],
    }
];

const VectorMap: React.FC<VectorMapProps> = ({ 
    center = [108.206230, 16.047079], 
    zoom = 13,
    className 
}) => {
    const mapContainer = useRef<HTMLDivElement>(null);
    const map = useRef<maplibregl.Map | null>(null);

    useEffect(() => {
        if (!mapContainer.current || map.current) return;

        map.current = new maplibregl.Map({
            container: mapContainer.current,
            // Use OpenFreeMap - completely free, no API key, English labels
            style: {
                version: 8,
                name: 'Vietnam Sovereignty Map',
                sources: {
                    'openmaptiles': {
                        type: 'vector',
                        url: 'https://tiles.openfreemap.org/planet'
                    }
                },
                // Custom style - English/Latin labels only
                layers: [
                    {
                        id: 'background',
                        type: 'background',
                        paint: { 'background-color': '#f8f4f0' }
                    },
                    {
                        id: 'water',
                        type: 'fill',
                        source: 'openmaptiles',
                        'source-layer': 'water',
                        paint: { 'fill-color': '#a0c8f0' }
                    },
                    {
                        id: 'landcover',
                        type: 'fill',
                        source: 'openmaptiles',
                        'source-layer': 'landcover',
                        paint: { 'fill-color': '#e8f0e8' }
                    },
                    {
                        id: 'park',
                        type: 'fill',
                        source: 'openmaptiles',
                        'source-layer': 'park',
                        paint: { 'fill-color': '#d0e8d0' }
                    },
                    {
                        id: 'landuse',
                        type: 'fill',
                        source: 'openmaptiles',
                        'source-layer': 'landuse',
                        paint: { 'fill-color': '#f0f0e8' }
                    },
                    {
                        id: 'boundary',
                        type: 'line',
                        source: 'openmaptiles',
                        'source-layer': 'boundary',
                        paint: {
                            'line-color': '#a0a0a0',
                            'line-width': 1,
                            'line-dasharray': [2, 2]
                        }
                    },
                    {
                        id: 'road-minor',
                        type: 'line',
                        source: 'openmaptiles',
                        'source-layer': 'transportation',
                        filter: ['==', 'class', 'minor'],
                        paint: {
                            'line-color': '#ffffff',
                            'line-width': 1
                        }
                    },
                    {
                        id: 'road-major',
                        type: 'line',
                        source: 'openmaptiles',
                        'source-layer': 'transportation',
                        filter: ['in', 'class', 'primary', 'secondary', 'tertiary'],
                        paint: {
                            'line-color': '#ffd700',
                            'line-width': 2
                        }
                    },
                    {
                        id: 'road-motorway',
                        type: 'line',
                        source: 'openmaptiles',
                        'source-layer': 'transportation',
                        filter: ['==', 'class', 'motorway'],
                        paint: {
                            'line-color': '#ff8c00',
                            'line-width': 3
                        }
                    },
                    {
                        id: 'building',
                        type: 'fill',
                        source: 'openmaptiles',
                        'source-layer': 'building',
                        paint: { 'fill-color': '#d8d8d8' }
                    },
                    // Place labels - USE LATIN NAME ONLY (no Chinese)
                    {
                        id: 'place-label',
                        type: 'symbol',
                        source: 'openmaptiles',
                        'source-layer': 'place',
                        layout: {
                            // Use name:latin or name:en, fallback to name
                            'text-field': ['coalesce', ['get', 'name:latin'], ['get', 'name:en'], ['get', 'name']],
                            'text-font': ['Open Sans Regular'],
                            'text-size': [
                                'interpolate', ['linear'], ['zoom'],
                                4, 10,
                                10, 14
                            ]
                        },
                        paint: {
                            'text-color': '#333333',
                            'text-halo-color': '#ffffff',
                            'text-halo-width': 1
                        }
                    }
                ],
                glyphs: 'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf'
            },
            center: center,
            zoom: zoom,
            attributionControl: false
        });

        // Add attribution
        map.current.addControl(new maplibregl.AttributionControl({
            customAttribution: '© OpenMapTiles © OpenStreetMap | 🇻🇳 Hoàng Sa, Trường Sa thuộc Việt Nam'
        }));

        // Add navigation controls
        map.current.addControl(new maplibregl.NavigationControl(), 'top-right');

        // Add Vietnam sovereignty markers
        map.current.on('load', () => {
            VIETNAM_ISLANDS.forEach(island => {
                // Create custom marker element
                const el = document.createElement('div');
                el.innerHTML = `
                    <div style="
                        background: rgba(255,255,255,0.95);
                        padding: 8px 12px;
                        border-radius: 8px;
                        border: 2px solid #dc2626;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                        text-align: center;
                        white-space: nowrap;
                    ">
                        <div style="font-weight: 600; color: #dc2626; font-size: 13px;">🇻🇳 ${island.name}</div>
                        <div style="font-size: 10px; color: #666;">${island.nameEn}</div>
                        <div style="font-size: 9px; color: #059669;">Việt Nam</div>
                    </div>
                `;

                new maplibregl.Marker({ element: el })
                    .setLngLat(island.coordinates)
                    .setPopup(new maplibregl.Popup().setHTML(`
                        <strong style="color: #dc2626;">${island.name}</strong><br/>
                        <span style="color: #666;">${island.nameEn}</span><br/>
                        <span style="color: #059669;">Thuộc chủ quyền Việt Nam</span>
                    `))
                    .addTo(map.current!);
            });
        });

        return () => {
            map.current?.remove();
            map.current = null;
        };
    }, [center, zoom]);

    return (
        <div 
            ref={mapContainer} 
            className={className || 'w-full h-[500px]'} 
            style={{ borderRadius: '12px' }}
        />
    );
};

export default VectorMap;
