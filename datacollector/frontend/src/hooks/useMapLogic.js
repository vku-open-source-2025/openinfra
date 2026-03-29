import { useState, useEffect, useCallback } from 'react';
import apiClient from '../services/apiClient';
import { MAP_CENTER as DEFAULT_CENTER, MAP_ZOOM as DEFAULT_ZOOM, INFRASTRUCTURE_TYPES } from '../constants';

export function useMapLogic() {
    const [features, setFeatures] = useState([]);
    const [pendingFeatures, setPendingFeatures] = useState([]);
    const [currentZoom, setCurrentZoom] = useState(DEFAULT_ZOOM);
    const [mapCenter, setMapCenter] = useState(DEFAULT_CENTER);
    
    // Missing state fixed here
    const [selectedType, setSelectedType] = useState(Object.keys(INFRASTRUCTURE_TYPES)[0]);
    const [featureProperties, setFeatureProperties] = useState({});
    const [currentLinePoints, setCurrentLinePoints] = useState([]);
    const [showAllFeatures, setShowAllFeatures] = useState(true);
    const [showExportModal, setShowExportModal] = useState(false);
    const [selectedExportTypes, setSelectedExportTypes] = useState([]);

    const fetchFeatures = useCallback(async () => {
        try {
            const response = await apiClient.get('/api/features');
            // Backend returns FeatureCollection, extract features array
            setFeatures(response.data.features || []);
        } catch (error) {
            console.error("Error fetching features:", error);
        }
    }, []);

    useEffect(() => {
        fetchFeatures();
    }, [fetchFeatures]);

    const addPendingFeature = (feature) => {
        setPendingFeatures(prev => [...prev, feature]);
    };

    const focusFeature = (feature) => {
        if (!feature || !feature.geometry || !feature.geometry.coordinates) return;
        
        try {
            if (feature.geometry.type === 'Point') {
                const [lng, lat] = feature.geometry.coordinates;
                if (lat !== undefined && lng !== undefined) {
                    setMapCenter([lat, lng]);
                    setCurrentZoom(18);
                }
            } else if (feature.geometry.type === 'LineString') {
                const coords = feature.geometry.coordinates;
                if (coords && coords.length > 0) {
                    setMapCenter([coords[0][1], coords[0][0]]);
                    setCurrentZoom(18);
                }
            } else if (feature.geometry.type === 'Polygon') {
                const coords = feature.geometry.coordinates[0];
                if (coords && coords.length > 0) {
                    setMapCenter([coords[0][1], coords[0][0]]);
                    setCurrentZoom(18);
                }
            }
        } catch (e) {
            console.error("Error focusing feature:", e);
        }
    };

    // Map Click Handler
    const handleMapClick = (e) => {
        const { lat, lng } = e.latlng;
        const typeConfig = INFRASTRUCTURE_TYPES[selectedType];

        if (typeConfig.type === "Point") {
            const newFeature = {
                type: "Feature",
                properties: {
                    feature_type: selectedType,
                    ...featureProperties,
                    created_at: new Date().toISOString()
                },
                geometry: {
                    type: "Point",
                    coordinates: [lng, lat]
                }
            };
            addPendingFeature(newFeature);
        } else if (typeConfig.type === "LineString") {
            setCurrentLinePoints(prev => [...prev, [lat, lng]]);
        }
    };

    const finishLine = () => {
        if (currentLinePoints.length < 2) return;
        
        const newFeature = {
            type: "Feature",
            properties: {
                feature_type: selectedType,
                ...featureProperties,
                created_at: new Date().toISOString()
            },
            geometry: {
                type: "LineString",
                coordinates: currentLinePoints.map(pt => [pt[1], pt[0]]) // Swap back to [lng, lat] for GeoJSON
            }
        };
        addPendingFeature(newFeature);
        setCurrentLinePoints([]);
    };

    const onDragPoint = (idx, newLatLng) => {
        setPendingFeatures(prev => {
            const updated = [...prev];
            updated[idx].geometry.coordinates = [newLatLng.lng, newLatLng.lat];
            return updated;
        });
    };

    const onDragLineVertex = (featureIdx, vertexIdx, newLatLng) => {
        setPendingFeatures(prev => {
            const updated = [...prev];
            const feature = updated[featureIdx];
            if (feature.geometry.type === "LineString") {
                feature.geometry.coordinates[vertexIdx] = [newLatLng.lng, newLatLng.lat];
            }
            return updated;
        });
    };

    return {
        features,
        setFeatures,
        pendingFeatures,
        setPendingFeatures,
        currentZoom,
        setCurrentZoom,
        mapCenter,
        setMapCenter,
        fetchFeatures,
        addPendingFeature,
        focusFeature,
        
        // New exports
        selectedType,
        setSelectedType,
        featureProperties,
        setFeatureProperties,
        currentLinePoints,
        setCurrentLinePoints,
        showAllFeatures,
        setShowAllFeatures,
        handleMapClick,
        finishLine,
        onDragPoint,
        onDragLineVertex,
        showExportModal,
        setShowExportModal,
        selectedExportTypes,
        setSelectedExportTypes
    };
}
