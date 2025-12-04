import React, {
    useState,
    useEffect,
    useRef,
    useMemo,
    useCallback,
} from "react";
import {
    MapContainer,
    TileLayer,
    Marker,
    Popup,
    Polyline,
    useMap,
    useMapEvents,
} from "react-leaflet";
import { type Asset, getAssetId } from "../api";
import { getIconForAsset, getColorForFeatureCode } from "../utils/mapIcons";
import HeatmapLayer from "./HeatmapLayer";
import AssetLayerFilter from "./AssetLayerFilter";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

// Disable default Leaflet marker icons to prevent showing default markers
// eslint-disable-next-line @typescript-eslint/no-explicit-any
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: undefined,
    iconUrl: undefined,
    shadowUrl: undefined,
});

// VietMap API key from environment
const VIETMAP_API_KEY = import.meta.env.VITE_VIETMAP_API_KEY || "";

interface MapProps {
    assets: Asset[];
    onAssetSelect: (asset: Asset | null) => void;
    onFilterByShape?: (assets: Asset[] | null) => void;
    routePoints?: Asset[]; // For routing feature
    selectedAsset?: Asset | null;
    className?: string;
    enableGeoSearches?: boolean;
}

const toLatLng = (coord: number[]): [number, number] => [coord[1], coord[0]];

const geometryToLatLngs = (geometry: Asset["geometry"]): [number, number][] => {
    if (!geometry || !geometry.coordinates) return [];

    switch (geometry.type) {
        case "Point":
            return [toLatLng(geometry.coordinates as number[])];
        case "LineString":
            return (geometry.coordinates as number[][]).map(toLatLng);
        case "MultiLineString":
            return (geometry.coordinates as number[][][]).flatMap((line) =>
                line.map(toLatLng)
            );
        case "Polygon":
            return (geometry.coordinates as number[][][])[0].map(toLatLng); // outer ring is enough for bounds
        case "MultiPolygon":
            return (geometry.coordinates as number[][][][]).flatMap((poly) =>
                poly[0].map(toLatLng)
            );
        case "MultiPoint":
            return (geometry.coordinates as number[][]).map(toLatLng);
        default:
            return [];
    }
};

const latLngsToBounds = (
    latLngs: [number, number][]
): L.LatLngBounds | null => {
    if (!latLngs.length) return null;
    const points = latLngs.map(([lat, lng]) => L.latLng(lat, lng));
    return L.latLngBounds(points);
};

const MapUpdater: React.FC<{
    selectedAsset: Asset | null;
    markerRefs: React.MutableRefObject<{ [key: string]: L.Marker | null }>;
}> = ({ selectedAsset, markerRefs }) => {
    const map = useMap();

    useEffect(() => {
        if (!selectedAsset) return;

        if (selectedAsset.geometry.type === "Point") {
            const [lng, lat] = selectedAsset.geometry.coordinates as number[];

            // Fly to the asset
            map.flyTo([lat, lng], 18, {
                animate: true,
                duration: 1.5,
            });

            // Open popup if marker exists
            const marker = markerRefs.current[getAssetId(selectedAsset)];
            if (marker) {
                // Small timeout to ensure flyTo starts/completes or just to be safe with UI updates
                setTimeout(() => {
                    marker.openPopup();
                }, 500);
            }
            return;
        }

        // For non-Point geometries, fit bounds to the shape
        const latLngs = geometryToLatLngs(selectedAsset.geometry);
        if (latLngs.length) {
            const bounds = latLngsToBounds(latLngs);
            if (bounds) {
                map.fitBounds(bounds, { padding: [50, 50], maxZoom: 18 });
            }
        }
    }, [selectedAsset, map, markerRefs]);

    return null;
};

const BoundsWatcher: React.FC<{
    onBoundsChange: (bounds: L.LatLngBounds) => void;
}> = ({ onBoundsChange }) => {
    const map = useMapEvents({
        moveend: () => onBoundsChange(map.getBounds()),
        zoomend: () => onBoundsChange(map.getBounds()),
        resize: () => onBoundsChange(map.getBounds()),
    });

    useEffect(() => {
        onBoundsChange(map.getBounds());
    }, [map, onBoundsChange]);

    return null;
};

const MapComponent: React.FC<MapProps> = ({
    assets,
    onAssetSelect,
    onFilterByShape,
    routePoints,
    selectedAsset,
    className,
    enableGeoSearches,
}) => {
    const [mapMode, setMapMode] = useState<"markers" | "heatmap">("markers");
    const center: [number, number] = [16.047079, 108.20623];
    const markerRefs = useRef<{ [key: string]: L.Marker | null }>({});
    const [mapBounds, setMapBounds] = useState<L.LatLngBounds | null>(null);
    const [filteredAssets, setFilteredAssets] = useState<Asset[]>(assets);

    // Prepare heatmap data
    const heatmapPoints = assets
        .filter(
            (a) =>
                a.geometry.type === "Point" &&
                Array.isArray(a.geometry.coordinates) &&
                a.geometry.coordinates.length >= 2
        )
        .map(
            (a) =>
                [a.geometry.coordinates[1], a.geometry.coordinates[0], 0.5] as [
                    number,
                    number,
                    number
                ]
        );

    const assetIntersectsBounds = useCallback(
        (asset: Asset, bounds: L.LatLngBounds) => {
            const latLngs = geometryToLatLngs(asset.geometry);
            if (!latLngs.length) return false;
            const assetBounds = latLngsToBounds(latLngs);
            if (!assetBounds) return false;
            return bounds.intersects(assetBounds);
        },
        []
    );

    // Update filtered assets when assets prop changes
    useEffect(() => {
        setFilteredAssets(assets);
    }, [assets]);

    const visibleAssets = useMemo(() => {
        if (!mapBounds) return filteredAssets;
        const filtered = filteredAssets.filter((asset) =>
            assetIntersectsBounds(asset, mapBounds)
        );

        // Always include selected asset even if currently out of bounds (so it renders after fitBounds)
        if (
            selectedAsset &&
            !filtered.find((a) => getAssetId(a) === getAssetId(selectedAsset))
        ) {
            filtered.push(selectedAsset);
        }

        return filtered;
    }, [filteredAssets, assetIntersectsBounds, mapBounds, selectedAsset]);

    return (
        <div
            className={`w-full relative group ${
                className || "h-[calc(100vh-250px)]"
            }`}
        >
            {/* Asset Layer Filter */}
            <AssetLayerFilter
                assets={assets}
                onFilterChange={setFilteredAssets}
            />

            {/* Map Controls Overlay */}
            <div className="absolute top-4 right-4 z-[1000] bg-white rounded-lg shadow-md border border-slate-200 p-1 flex flex-col gap-1">
                <button
                    onClick={() => setMapMode("markers")}
                    className={`p - 2 rounded hover: bg - slate - 100 ${
                        mapMode === "markers"
                            ? "bg-blue-50 text-blue-600"
                            : "text-slate-600"
                    } `}
                    title="Marker View"
                >
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="20"
                        height="20"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    >
                        <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z" />
                        <circle cx="12" cy="10" r="3" />
                    </svg>
                </button>
                <button
                    onClick={() => setMapMode("heatmap")}
                    className={`p - 2 rounded hover: bg - slate - 100 ${
                        mapMode === "heatmap"
                            ? "bg-blue-50 text-blue-600"
                            : "text-slate-600"
                    } `}
                    title="Heatmap View"
                >
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="20"
                        height="20"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    >
                        <path d="M12 20a8 8 0 1 0 0-16 8 8 0 0 0 0 16Z" />
                        <path d="M12 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z" />
                        <path d="M12 2v2" />
                        <path d="M12 22v-2" />
                        <path d="M2 12h2" />
                        <path d="M22 12h-2" />
                        <path d="M4.93 4.93l1.41 1.41" />
                        <path d="M17.66 17.66l1.41 1.41" />
                        <path d="M4.93 19.07l1.41-1.41" />
                        <path d="M17.66 6.34l1.41 1.41" />
                    </svg>
                </button>
            </div>

            <MapContainer
                center={center}
                zoom={16}
                maxZoom={20}
                scrollWheelZoom={true}
                className="h-full w-full rounded-xl shadow-sm border border-slate-200"
            >
                <MapUpdater
                    selectedAsset={selectedAsset || null}
                    markerRefs={markerRefs}
                />
                <BoundsWatcher onBoundsChange={setMapBounds} />
                {/* Map Tile Layer (VietMap with fallback to OpenStreetMap) */}
                {VIETMAP_API_KEY ? (
                    <TileLayer
                        attribution='&copy; <a href="https://vietmap.vn">VietMap</a> | Hoang Sa and Truong Sa belong to Vietnam 🇻🇳'
                        url={`https://maps.vietmap.vn/maps/tiles/tm/{z}/{x}/{y}@2x.png?apikey=${VIETMAP_API_KEY}`}
                    />
                ) : (
                    <TileLayer
                        attribution='&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        maxZoom={20}
                        maxNativeZoom={16}
                    />
                )}

                {mapMode === "markers" && (
                    <>
                        {visibleAssets.map((asset) => {
                            if (asset.geometry.type === "Point") {
                                const position: [number, number] = [
                                    asset.geometry.coordinates[1],
                                    asset.geometry.coordinates[0],
                                ];
                                const assetId = getAssetId(asset);
                                const isSelected =
                                    selectedAsset && getAssetId(selectedAsset) === assetId;
                                return (
                                    <Marker
                                        key={assetId}
                                        position={position}
                                        icon={getIconForAsset(
                                            asset.feature_code,
                                            isSelected
                                        )}
                                        eventHandlers={{
                                            click: () => onAssetSelect(asset),
                                        }}
                                        ref={(el) => {
                                            if (el) {
                                                markerRefs.current[assetId] =
                                                    el;
                                            }
                                        }}
                                    >
                                        <Popup className="custom-popup">
                                            <div className="font-semibold text-slate-900">
                                                {asset.feature_type}
                                            </div>
                                            <div className="text-xs text-slate-500">
                                                {asset.feature_code}
                                            </div>
                                            <div className="mt-2 text-xs">
                                                <span
                                                    className={`px-2 py-0.5 rounded-full ${
                                                        Math.random() > 0.1
                                                            ? "bg-green-100 text-green-700"
                                                            : "bg-red-100 text-red-700"
                                                    }`}
                                                >
                                                    {Math.random() > 0.1
                                                        ? "Online"
                                                        : "Offline"}
                                                </span>
                                            </div>
                                        </Popup>
                                    </Marker>
                                );
                            }
                            return null;
                        })}
                        {visibleAssets.map((asset) => {
                            if (asset.geometry.type === "LineString") {
                                const positions =
                                    asset.geometry.coordinates.map(
                                        (coord: any) =>
                                            [coord[1], coord[0]] as [
                                                number,
                                                number
                                            ]
                                    );
                                const color = getColorForFeatureCode(
                                    asset.feature_code
                                );
                                return (
                                    <Polyline
                                        key={getAssetId(asset)}
                                        positions={positions}
                                        color={color}
                                        weight={4}
                                        opacity={0.8}
                                        eventHandlers={{
                                            click: () => {
                                                console.log(
                                                    "LineString clicked:",
                                                    asset
                                                );
                                                console.log(
                                                    "Geometry type:",
                                                    asset.geometry.type
                                                );
                                                console.log(
                                                    "Coordinates:",
                                                    asset.geometry.coordinates
                                                );
                                                onAssetSelect(asset);
                                            },
                                        }}
                                    >
                                        <Popup className="custom-popup">
                                            <div className="font-semibold text-slate-900">
                                                {asset.feature_type}
                                            </div>
                                            <div className="text-xs text-slate-500">
                                                {asset.feature_code}
                                            </div>
                                        </Popup>
                                    </Polyline>
                                );
                            }
                            return null;
                        })}
                    </>
                )}

                {mapMode === "heatmap" && (
                    <HeatmapLayer points={heatmapPoints} />
                )}

                {routePoints && routePoints.length > 1 && (
                    <Polyline
                        positions={routePoints.map((a) => [
                            a.geometry.coordinates[1],
                            a.geometry.coordinates[0],
                        ])}
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
