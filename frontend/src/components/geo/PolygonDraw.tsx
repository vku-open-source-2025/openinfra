import React, { useState, useCallback, useEffect } from "react";
import { Layers, X, Check } from "lucide-react";
import { Button } from "../ui/button";
import { geoApi } from "../../api/geo";
import type { Asset } from "../../types";
import L from "leaflet";
import "leaflet-draw";

interface PolygonDrawProps {
    map: L.Map;
    onResults: (assets: Asset[]) => void;
    onClear?: () => void;
}

export const PolygonDraw: React.FC<PolygonDrawProps> = ({
    map,
    onResults,
    onClear,
}) => {
    const [isDrawing, setIsDrawing] = useState(false);
    const [drawnPolygon, setDrawnPolygon] = useState<L.Polygon | null>(null);
    const [drawControl, setDrawControl] = useState<L.Control.Draw | null>(null);
    const [isSearching, setIsSearching] = useState(false);

    useEffect(() => {
        if (!isDrawing) return;

        const drawControlInstance = new L.Control.Draw({
            position: "topleft",
            draw: {
                rectangle: false,
                circle: false,
                circlemarker: false,
                marker: false,
                polyline: false,
                polygon: {
                    allowIntersection: false,
                    showArea: true,
                    shapeOptions: {
                        color: "#3b82f6",
                        fillColor: "#3b82f6",
                        fillOpacity: 0.2,
                        weight: 2,
                    },
                },
            },
            edit: {
                featureGroup: new L.FeatureGroup(),
                remove: true,
            },
        });

        drawControlInstance.addTo(map);
        setDrawControl(drawControlInstance);

        const handleDrawStart = () => {
            // Clear previous polygon if exists
            if (drawnPolygon) {
                map.removeLayer(drawnPolygon);
                setDrawnPolygon(null);
            }
        };

        const handleDrawCreated = async (e: L.DrawEvents.Created) => {
            const layer = e.layer;
            const geoJson = layer.toGeoJSON();

            if (
                geoJson.type === "Feature" &&
                geoJson.geometry.type === "Polygon"
            ) {
                const coordinates = (
                    geoJson.geometry.coordinates[0] as number[][]
                ).map((coord) => [coord[0], coord[1]]);

                // Add polygon to map with custom styling
                const polygon = L.polygon(
                    coordinates.map(
                        ([lng, lat]) => [lat, lng] as [number, number]
                    ),
                    {
                        color: "#3b82f6",
                        fillColor: "#3b82f6",
                        fillOpacity: 0.2,
                        weight: 2,
                    }
                ).addTo(map);

                setDrawnPolygon(polygon);

                // Search for assets within polygon
                setIsSearching(true);
                try {
                    const results = await geoApi.findAssetsInPolygon({
                        coordinates: coordinates,
                    });
                    onResults(results);

                    // Fit bounds to polygon
                    map.fitBounds(polygon.getBounds().pad(0.1));
                } catch (error) {
                    console.error("Polygon search failed:", error);
                } finally {
                    setIsSearching(false);
                }
            }

            // Remove draw control after drawing
            if (drawControlInstance) {
                map.removeControl(drawControlInstance);
                setDrawControl(null);
                setIsDrawing(false);
            }
        };

        map.on(L.Draw.Event.DRAWSTART, handleDrawStart);
        map.on(L.Draw.Event.CREATED, handleDrawCreated);

        return () => {
            map.off(L.Draw.Event.DRAWSTART, handleDrawStart);
            map.off(L.Draw.Event.CREATED, handleDrawCreated);
            if (drawControlInstance) {
                map.removeControl(drawControlInstance);
            }
        };
    }, [map, isDrawing, drawnPolygon, onResults]);

    const handleStartDrawing = useCallback(() => {
        setIsDrawing(true);
    }, []);

    const handleClear = useCallback(() => {
        if (drawnPolygon) {
            map.removeLayer(drawnPolygon);
            setDrawnPolygon(null);
        }
        if (drawControl) {
            map.removeControl(drawControl);
            setDrawControl(null);
        }
        setIsDrawing(false);
        if (onClear) {
            onClear();
        }
    }, [map, drawnPolygon, drawControl, onClear]);

    return (
        <div className="relative bg-white rounded-lg shadow-lg border border-slate-200">
            {!isDrawing ? (
                <Button
                    onClick={handleStartDrawing}
                    variant="outline"
                    size="sm"
                    className="flex items-center gap-2"
                >
                    <Layers size={16} />
                    Vẽ khu vực
                </Button>
            ) : (
                <div className="p-3 flex items-center gap-2">
                    <div className="flex items-center gap-2 text-sm text-slate-600">
                        {isSearching ? (
                            <>
                                <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                                <span>Đang tìm...</span>
                            </>
                        ) : (
                            <>
                                <Layers size={16} />
                                <span>Nhấn vào bản đồ để vẽ đa giác</span>
                            </>
                        )}
                    </div>
                    <Button
                        onClick={handleClear}
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0"
                    >
                        <X size={14} />
                    </Button>
                </div>
            )}
        </div>
    );
};
