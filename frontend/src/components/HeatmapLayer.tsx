import { useEffect } from "react";
import L from "leaflet";
import "leaflet.heat";

interface HeatmapLayerProps {
    map: L.Map;
    points: [number, number, number][]; // lat, lng, intensity
}

type LeafletWithHeat = typeof L & {
    heatLayer: (
        points: [number, number, number][],
        options: {
            radius: number;
            blur: number;
            maxZoom: number;
        }
    ) => L.Layer;
};

const HeatmapLayer = ({ map, points }: HeatmapLayerProps) => {
    useEffect(() => {
        if (!points.length) return;

        const leafletWithHeat = L as LeafletWithHeat;

        const heat = leafletWithHeat.heatLayer(points, {
            radius: 25,
            blur: 15,
            maxZoom: 10,
        });

        heat.addTo(map);

        return () => {
            map.removeLayer(heat);
        };
    }, [points, map]);

    return null;
};

export default HeatmapLayer;
