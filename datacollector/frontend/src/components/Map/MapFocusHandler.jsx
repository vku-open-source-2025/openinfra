import { useEffect } from 'react';
import { useMap } from 'react-leaflet';

export const MapFocusHandler = ({ flyTo }) => {
    const map = useMap();
    useEffect(() => {
        if (flyTo) {
            map.flyTo(flyTo, 18, { duration: 1.5 });
        }
    }, [flyTo, map]);
    return null;
};
