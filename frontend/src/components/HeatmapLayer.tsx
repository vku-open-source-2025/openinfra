import { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet.heat';

interface HeatmapLayerProps {
    points: [number, number, number][]; // lat, lng, intensity
}

const HeatmapLayer = ({ points }: HeatmapLayerProps) => {
    const map = useMap();

    useEffect(() => {
        if (!points.length) return;

        const heat = (L as any).heatLayer(points, {
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
