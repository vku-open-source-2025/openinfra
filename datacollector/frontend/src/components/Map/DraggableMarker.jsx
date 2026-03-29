import React, { useRef, useMemo } from 'react';
import { Marker } from 'react-leaflet';
import L from 'leaflet';

export function DraggableMarker({ position, onDragEnd, icon = null }) {
    const markerRef = useRef(null);
    const eventHandlers = useMemo(
      () => ({
        dragend() {
          const marker = markerRef.current;
          if (marker != null) {
            onDragEnd(marker.getLatLng());
          }
        },
      }),
      [onDragEnd],
    );
  
    return (
      <Marker
        draggable={true}
        eventHandlers={eventHandlers}
        position={position}
        ref={markerRef}
        icon={icon || new L.Icon.Default()}
      />
    );
}
