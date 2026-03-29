import React, { useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Polyline, Popup, LayerGroup, CircleMarker } from 'react-leaflet';
import L from 'leaflet';
import { INFRASTRUCTURE_TYPES, MAP_STYLE, MAP_CENTER, MAP_ZOOM, ZOOM_THRESHOLD } from '../../constants';
import { createCustomIcon } from '../../utils/mapUtils';
import { MapClickHandler } from './MapClickHandler';
import { MapFocusHandler } from './MapFocusHandler';
import { DraggableMarker } from './DraggableMarker';
import { API_URL } from '../../config';

export const MapView = ({ 
  dbFeatures, 
  pendingFeatures, 
  reviewFeatures = [], 
  currentLinePoints, 
  handleMapClick,
  onDragPoint, 
  onDragLineVertex,
  showAllFeatures,
  currentZoom,
  onZoomChange,
  onDeleteFeature,
  isAdmin = false,
  flyTo = null
}) => {
  
  const visibleDbFeatures = useMemo(() => {
    if (showAllFeatures) return dbFeatures;
    if (currentZoom >= ZOOM_THRESHOLD) return dbFeatures;
    return [];
  }, [dbFeatures, showAllFeatures, currentZoom]);

  console.log("MapView visibleDbFeatures:", visibleDbFeatures);

  return (
    <MapContainer center={MAP_CENTER} zoom={MAP_ZOOM} style={MAP_STYLE} scrollWheelZoom={true}>
      <TileLayer
        url={`${API_URL}/api/map/tiles/{z}/{x}/{y}`}
        maxZoom={20}
        attribution='&copy; <a href="https://vietmap.vn">VietMap</a> | Hoang Sa and Truong Sa belong to Vietnam 🇻🇳'
      />
      <MapClickHandler onMapClick={handleMapClick} onZoomEnd={onZoomChange} />
      <MapFocusHandler flyTo={flyTo} />

      {/* Render Database Features */}
      {Array.isArray(visibleDbFeatures) && visibleDbFeatures.map((feature, idx) => {
         if (!feature || !feature.properties || !feature.geometry || !feature.geometry.coordinates) return null;
         
         const color = INFRASTRUCTURE_TYPES[feature.properties.feature_type]?.color || 'blue';
         const featureCode = INFRASTRUCTURE_TYPES[feature.properties.feature_type]?.code;
         const featureId = feature._id || feature.id;

         // Safety check for coordinates
         if (feature.geometry.type === "Point" && feature.geometry.coordinates.length < 2) return null;

         return feature.geometry.type === "Point" ? (
            <Marker 
                key={`db-${featureId || idx}`} 
                position={[feature.geometry.coordinates[1], feature.geometry.coordinates[0]]}
                icon={createCustomIcon(color, false, false, featureCode)}
            >
                <Popup>
                    <b>{feature.properties.feature_type}</b>
                    <br/>
                    <small>Code: {feature.feature_code || 'N/A'}</small>
                    <pre>{JSON.stringify(feature.properties, null, 2)}</pre>
                    {isAdmin && <button onClick={() => onDeleteFeature(featureId, false)} style={{color: 'red', marginTop: '5px'}}>Delete</button>}
                </Popup>
            </Marker>
         ) : feature.geometry.type === "LineString" ? (
            <Polyline
                key={`db-${featureId || idx}`}
                positions={feature.geometry.coordinates.map(c => [c[1], c[0]])}
                color={color}
            >
                <Popup>
                    <b>{feature.properties.feature_type}</b>
                    <br/>
                    <small>Code: {feature.feature_code || 'N/A'}</small>
                    <pre>{JSON.stringify(feature.properties, null, 2)}</pre>
                    {isAdmin && <button onClick={() => onDeleteFeature(featureId, false)} style={{color: 'red', marginTop: '5px'}}>Delete</button>}
                </Popup>
            </Polyline>
         ) : null
      })}

      {/* Render Review Features (Contributions) - Read Only */}
      {Array.isArray(reviewFeatures) && reviewFeatures.map((feature, idx) => {
         if (!feature || !feature.properties || !feature.geometry || !feature.geometry.coordinates) return null;
         const color = INFRASTRUCTURE_TYPES[feature.properties.feature_type]?.color || 'orange';
         const featureCode = INFRASTRUCTURE_TYPES[feature.properties.feature_type]?.code;
         
         // Safety check for coordinates
         if (feature.geometry.type === "Point" && feature.geometry.coordinates.length < 2) return null;
         
         return feature.geometry.type === "Point" ? (
            <Marker
                key={`review-${idx}`}
                position={[feature.geometry.coordinates[1], feature.geometry.coordinates[0]]}
                icon={createCustomIcon(color, true, true, featureCode)} 
                opacity={0.7}
            >
                <Popup>
                    <b>PENDING REVIEW: {feature.properties.feature_type}</b>
                    <p>Contributor: {feature.contributor_name} ({feature.msv})</p>
                    <pre>{JSON.stringify(feature.properties, null, 2)}</pre>
                </Popup>
            </Marker>
         ) : (
            <Polyline
                key={`review-${idx}`}
                positions={feature.geometry.coordinates.map(c => [c[1], c[0]])}
                color={color}
                dashArray="10, 5"
                opacity={0.85}
                weight={4}
            >
                 <Popup>
                    <b>PENDING REVIEW: {feature.properties.feature_type}</b>
                    <p>Contributor: {feature.contributor_name} ({feature.msv})</p>
                    <pre>{JSON.stringify(feature.properties, null, 2)}</pre>
                </Popup>
            </Polyline>
         )
      })}

      {/* Render Pending Features (Editable Drafts) */}
      {Array.isArray(pendingFeatures) && pendingFeatures.map((feature, idx) => {
         const color = INFRASTRUCTURE_TYPES[feature.properties.feature_type]?.color || 'orange';
         const featureCode = INFRASTRUCTURE_TYPES[feature.properties.feature_type]?.code;
         const isPoint = feature.geometry.type === "Point";
         
         return isPoint ? (
            <DraggableMarker 
                key={`pending-${idx}`} 
                position={[feature.geometry.coordinates[1], feature.geometry.coordinates[0]]}
                onDragEnd={(newLatLng) => onDragPoint(idx, newLatLng)}
                icon={createCustomIcon(color, true, false, featureCode)}
            />
         ) : (
            <LayerGroup key={`pending-${idx}`}>
                <Polyline
                    positions={feature.geometry.coordinates.map(c => [c[1], c[0]])}
                    color={color}
                    dashArray="8, 5"
                    opacity={0.8}
                    weight={3}
                />
                {feature.geometry.coordinates.map((coord, vIdx) => (
                    <DraggableMarker
                        key={`pending-${idx}-v-${vIdx}`}
                        position={[coord[1], coord[0]]}
                        onDragEnd={(newLatLng) => onDragLineVertex(idx, vIdx, newLatLng)}
                        icon={L.divIcon({className: 'line-vertex-icon', html: '<div style="width: 10px; height: 10px; background: red; border-radius: 50%;"></div>'})}
                    />
                ))}
            </LayerGroup>
         )
      })}

      {/* Render Current Line being drawn */}
      {currentLinePoints.length > 0 && (
        <>
            <Polyline positions={currentLinePoints} color="red" dashArray="5, 5" />
            {currentLinePoints.map((pt, idx) => (
                <CircleMarker key={`line-pt-${idx}`} center={pt} radius={3} color="red" />
            ))}
        </>
      )}
    </MapContainer>
  );
};
