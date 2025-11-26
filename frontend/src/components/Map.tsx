
import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, FeatureGroup, Polyline, useMap } from 'react-leaflet';
import MarkerClusterGroup from 'react-leaflet-cluster';
import { EditControl } from 'react-leaflet-draw';
import type { Asset } from '../api';
import { getIconForAsset } from '../utils/mapIcons';
import HeatmapLayer from './HeatmapLayer';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import * as turf from '@turf/turf';

interface MapProps {
    assets: Asset[];
    onAssetSelect: (asset: Asset) => void;
    onFilterByShape?: (filteredAssets: Asset[]) => void;
    routePoints?: Asset[]; // For routing feature
    selectedAsset?: Asset | null;
    className?: string;
}

const MapUpdater: React.FC<{ selectedAsset: Asset | null }> = ({ selectedAsset }) => {
    const map = useMap();

    useEffect(() => {
        if (selectedAsset && selectedAsset.geometry.type === 'Point') {
            const [lng, lat] = selectedAsset.geometry.coordinates;
            map.flyTo([lat, lng], 16, {
                animate: true,
                duration: 1.5
            });
        }
    }, [selectedAsset, map]);

    return null;
};

const MapComponent: React.FC<MapProps> = ({ assets, onAssetSelect, onFilterByShape, routePoints, selectedAsset, className }) => {
    const [mapMode, setMapMode] = useState<'markers' | 'heatmap'>('markers');
    const center: [number, number] = [16.047079, 108.206230];

    // Prepare heatmap data
    const heatmapPoints = assets
        .filter(a => a.geometry.type === 'Point')
        .map(a => [a.geometry.coordinates[1], a.geometry.coordinates[0], 0.5] as [number, number, number]);

    const _onCreated = (e: any) => {
        if (!onFilterByShape) return;

        const layer = e.layer;
        const shape = layer.toGeoJSON();

        // Filter assets within the shape
        const filtered = assets.filter(asset => {
            if (asset.geometry.type !== 'Point') return false;
            const pt = turf.point(asset.geometry.coordinates);
            return turf.booleanPointInPolygon(pt, shape);
        });

        onFilterByShape(filtered);
    };

    const _onDeleted = () => {
        if (onFilterByShape) onFilterByShape(assets);
    };

    return (
        <div className={`w-full relative group ${className || 'h-[calc(100vh-250px)]'}`}>
            {/* Map Controls Overlay */}
            <div className="absolute top-4 right-4 z-[1000] bg-white rounded-lg shadow-md border border-slate-200 p-1 flex flex-col gap-1">
                <button
                    onClick={() => setMapMode('markers')}
                    className={`p - 2 rounded hover: bg - slate - 100 ${mapMode === 'markers' ? 'bg-blue-50 text-blue-600' : 'text-slate-600'} `}
                    title="Marker View"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z" /><circle cx="12" cy="10" r="3" /></svg>
                </button>
                <button
                    onClick={() => setMapMode('heatmap')}
                    className={`p - 2 rounded hover: bg - slate - 100 ${mapMode === 'heatmap' ? 'bg-blue-50 text-blue-600' : 'text-slate-600'} `}
                    title="Heatmap View"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20a8 8 0 1 0 0-16 8 8 0 0 0 0 16Z" /><path d="M12 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z" /><path d="M12 2v2" /><path d="M12 22v-2" /><path d="M2 12h2" /><path d="M22 12h-2" /><path d="M4.93 4.93l1.41 1.41" /><path d="M17.66 17.66l1.41 1.41" /><path d="M4.93 19.07l1.41-1.41" /><path d="M17.66 6.34l1.41 1.41" /></svg>
                </button>
            </div>

            <MapContainer center={center} zoom={13} scrollWheelZoom={true} className="h-full w-full rounded-xl shadow-sm border border-slate-200">
                <MapUpdater selectedAsset={selectedAsset || null} />
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                />

                <FeatureGroup>
                    <EditControl
                        position="topleft"
                        onCreated={_onCreated}
                        onDeleted={_onDeleted}
                        draw={{
                            rectangle: false,
                            circle: false,
                            circlemarker: false,
                            marker: false,
                            polyline: false,
                            polygon: {
                                allowIntersection: false,
                                showArea: true,
                            },
                        }}
                    />
                </FeatureGroup>

                {mapMode === 'markers' && (
                    <MarkerClusterGroup chunkedLoading>
                        {assets.map((asset) => {
                            if (asset.geometry.type === 'Point') {
                                const position: [number, number] = [asset.geometry.coordinates[1], asset.geometry.coordinates[0]];
                                return (
                                    <Marker
                                        key={asset._id}
                                        position={position}
                                        icon={getIconForAsset(asset.feature_code)}
                                        eventHandlers={{
                                            click: () => onAssetSelect(asset),
                                        }}
                                    >
                                        <Popup className="custom-popup">
                                            <div className="font-semibold text-slate-900">{asset.feature_type}</div>
                                            <div className="text-xs text-slate-500">{asset.feature_code}</div>
                                            <div className="mt-2 text-xs">
                                                <span className={`px - 2 py - 0.5 rounded - full ${Math.random() > 0.1 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'} `}>
                                                    {Math.random() > 0.1 ? 'Online' : 'Offline'}
                                                </span>
                                            </div>
                                        </Popup>
                                    </Marker>
                                );
                            }
                            return null;
                        })}
                    </MarkerClusterGroup>
                )}

                {mapMode === 'heatmap' && (
                    <HeatmapLayer points={heatmapPoints} />
                )}

                {routePoints && routePoints.length > 1 && (
                    <Polyline
                        positions={routePoints.map(a => [a.geometry.coordinates[1], a.geometry.coordinates[0]])}
                        color="blue"
                        weight={4}
                        opacity={0.7}
                        dashArray="10, 10"
                    />
                )}
            </MapContainer>
        </div>
    );
};

export default MapComponent;

