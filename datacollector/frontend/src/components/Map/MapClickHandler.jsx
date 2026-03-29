import { useMapEvents } from 'react-leaflet';

export const MapClickHandler = ({ onMapClick, onZoomEnd }) => {
  useMapEvents({
    click: (e) => {
      console.log("Map clicked:", e.latlng);
      onMapClick(e);
    },
    zoomend: (e) => {
      onZoomEnd(e.target.getZoom());
    }
  });
  return null;
};
