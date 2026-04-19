import React, {
    useState,
    useEffect,
    useRef,
    useMemo,
    useCallback,
} from "react";
import { type Asset, getAssetId } from "../api";
import { getIconForAsset, getColorForFeatureCode } from "../utils/mapIcons";
import HeatmapLayer from "./HeatmapLayer";
import AssetLayerFilter from "./AssetLayerFilter";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { fetchTileConfig } from "../lib/tileConfig";

// Disable default Leaflet marker icons to prevent showing default markers
// eslint-disable-next-line @typescript-eslint/no-explicit-any
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: undefined,
    iconUrl: undefined,
    shadowUrl: undefined,
});

// ---------------------------------------------------------------------------
// Simple grid-based marker clustering (no extra library required)
// Groups Point assets of the same feature_code that fall in the same screen
// tile at the current zoom level.  Returns either individual assets (cluster
// size 1) or a synthetic cluster object.
// ---------------------------------------------------------------------------
interface ClusterItem {
    type: "single";
    asset: Asset;
}
interface ClusterGroup {
    type: "cluster";
    featureCode: string;
    count: number;
    lat: number;
    lng: number;
    assets: Asset[];
}
type ClusterEntry = ClusterItem | ClusterGroup;

/** Pixel grid cell size used for clustering (screen pixels). */
const CLUSTER_GRID_PX = 60;

function clusterAssets(
    assets: Asset[],
    map: L.Map,
    zoom: number
): ClusterEntry[] {
    const pointAssets = assets.filter((a) => a.geometry.type === "Point");
    // Group by feature_code then cluster within each group
    const byCode = new Map<string, Asset[]>();
    for (const a of pointAssets) {
        const list = byCode.get(a.feature_code) ?? [];
        list.push(a);
        byCode.set(a.feature_code, list);
    }

    const result: ClusterEntry[] = [];

    byCode.forEach((group) => {
        if (group.length <= 1) {
            group.forEach((a) => result.push({ type: "single", asset: a }));
            return;
        }

        // Only cluster when zoom < 17 (enough resolution to see individual items)
        if (zoom >= 17) {
            group.forEach((a) => result.push({ type: "single", asset: a }));
            return;
        }

        // Assign each asset to a grid cell using Leaflet's project()
        const cells = new Map<string, Asset[]>();
        for (const a of group) {
            const coords = a.geometry.coordinates as number[];
            const pt = map.project([coords[1], coords[0]], zoom);
            const cx = Math.floor(pt.x / CLUSTER_GRID_PX);
            const cy = Math.floor(pt.y / CLUSTER_GRID_PX);
            const key = `${cx}:${cy}`;
            const list = cells.get(key) ?? [];
            list.push(a);
            cells.set(key, list);
        }

        cells.forEach((cellAssets) => {
            if (cellAssets.length === 1) {
                result.push({ type: "single", asset: cellAssets[0] });
            } else {
                // Centroid
                let sumLat = 0, sumLng = 0;
                cellAssets.forEach((a) => {
                    const c = a.geometry.coordinates as number[];
                    sumLng += c[0];
                    sumLat += c[1];
                });
                result.push({
                    type: "cluster",
                    featureCode: cellAssets[0].feature_code,
                    count: cellAssets.length,
                    lat: sumLat / cellAssets.length,
                    lng: sumLng / cellAssets.length,
                    assets: cellAssets,
                });
            }
        });
    });

    return result;
}

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

    const coords = geometry.coordinates as unknown;
    switch (geometry.type) {
        case "Point":
            if (Array.isArray(coords) && typeof coords[0] === "number") {
                return [toLatLng(coords as number[])];
            }
            return [];
        case "LineString":
            if (
                Array.isArray(coords) &&
                Array.isArray(coords[0]) &&
                typeof coords[0][0] === "number"
            ) {
                return (coords as number[][]).map(toLatLng);
            }
            return [];
        case "MultiLineString":
            if (Array.isArray(coords)) {
                return (coords as number[][][]).flatMap((line) =>
                    (line as number[][]).map(toLatLng)
                );
            }
            return [];
        case "Polygon":
            if (
                Array.isArray(coords) &&
                Array.isArray(coords[0]) &&
                Array.isArray(coords[0][0])
            ) {
                return (coords as number[][][])[0].map(toLatLng);
            }
            return [];
        case "MultiPolygon":
            if (Array.isArray(coords)) {
                return (coords as number[][][][]).flatMap((poly) =>
                    (poly[0] as number[][]).map(toLatLng)
                );
            }
            return [];
        case "MultiPoint":
            if (
                Array.isArray(coords) &&
                Array.isArray(coords[0]) &&
                typeof coords[0][0] === "number"
            ) {
                return (coords as number[][]).map(toLatLng);
            }
            return [];
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

const MapComponent: React.FC<MapProps> = ({
    assets,
    onAssetSelect,
    routePoints,
    selectedAsset,
    className,
    // Not using onFilterByShape/enableGeoSearches yet - keep props for future features
}) => {
    const [mapMode, setMapMode] = useState<"markers" | "heatmap">("markers");
    const center: [number, number] = [16.047079, 108.20623];
    const mapRef = useRef<L.Map | null>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const markerRefs = useRef<{ [key: string]: L.Marker | null }>({});
    const polylineRefs = useRef<{ [key: string]: L.Polyline | null }>({});
    const routePolylineRef = useRef<L.Polyline | null>(null);
    const tileLayerRef = useRef<L.TileLayer | null>(null);
    const [mapBounds, setMapBounds] = useState<L.LatLngBounds | null>(null);
    const [mapZoom, setMapZoom] = useState<number>(16);
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

    // Initialize map
    useEffect(() => {
        if (!containerRef.current || mapRef.current) return;

        const map = L.map(containerRef.current, {
            center,
            zoom: 16,
            maxZoom: 20,
            scrollWheelZoom: true,
        });

        // Add tile layer (fetched from backend)
        mapRef.current = map;
        fetchTileConfig().then((cfg) => {
            if (!mapRef.current) return;
            const tileLayer = L.tileLayer(cfg.tileUrl, {
                attribution: cfg.attribution,
                maxZoom: cfg.maxZoom,
                ...(cfg.maxNativeZoom ? { maxNativeZoom: cfg.maxNativeZoom } : {}),
            });
            tileLayer.addTo(mapRef.current);
            tileLayerRef.current = tileLayer;
        });

        // Set initial bounds
        setMapBounds(map.getBounds());
        setMapZoom(map.getZoom());

        // Listen to map events for bounds updates
        const updateBounds = () => {
            setMapBounds(map.getBounds());
            setMapZoom(map.getZoom());
        };

        map.on("moveend", updateBounds);
        map.on("zoomend", updateBounds);
        map.on("resize", updateBounds);

        return () => {
            map.off("moveend", updateBounds);
            map.off("zoomend", updateBounds);
            map.off("resize", updateBounds);
            map.remove();
            mapRef.current = null;
        };
    }, []);

    // Handle selected asset changes - fly to or fit bounds
    useEffect(() => {
        if (!mapRef.current || !selectedAsset) return;

        const map = mapRef.current;

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
    }, [selectedAsset]);

    // Render markers and polylines
    useEffect(() => {
        if (!mapRef.current || mapMode !== "markers") return;

        const map = mapRef.current;

        // Clean up old markers and polylines
        Object.values(markerRefs.current).forEach((marker) => {
            if (marker) {
                map.removeLayer(marker);
            }
        });
        Object.values(polylineRefs.current).forEach((polyline) => {
            if (polyline) {
                map.removeLayer(polyline);
            }
        });
        markerRefs.current = {};
        polylineRefs.current = {};

        // Cluster Point assets by category, then render
        const clusters = clusterAssets(visibleAssets, map, mapZoom);

        clusters.forEach((entry) => {
            if (entry.type === "cluster") {
                // Render a cluster bubble
                const color = getColorForFeatureCode(entry.featureCode);
                const icon = L.divIcon({
                    html: `<div style="
                        background:${color};
                        color:#fff;
                        border-radius:50%;
                        width:36px;height:36px;
                        display:flex;align-items:center;justify-content:center;
                        font-size:13px;font-weight:700;
                        border:2px solid rgba(255,255,255,0.8);
                        box-shadow:0 2px 6px rgba(0,0,0,0.35);
                        cursor:pointer;
                    ">${entry.count}</div>`,
                    className: "",
                    iconSize: [36, 36],
                    iconAnchor: [18, 18],
                });
                const popupLines = entry.assets
                    .slice(0, 6)
                    .map(
                        (a) =>
                            `<div style="font-size:11px;padding:1px 0">${a.feature_type}</div>`
                    )
                    .join("");
                const more =
                    entry.assets.length > 6
                        ? `<div style="font-size:11px;color:#888">… và ${entry.assets.length - 6} cái nữa</div>`
                        : "";
                const clusterKey = `cluster:${entry.featureCode}:${entry.lat.toFixed(6)}:${entry.lng.toFixed(6)}`;
                const marker = L.marker([entry.lat, entry.lng], { icon })
                    .addTo(map)
                    .bindPopup(
                        `<div style="min-width:160px"><div style="font-weight:700;margin-bottom:4px">${entry.featureCode} (${entry.count})</div>${popupLines}${more}</div>`,
                        { className: "custom-popup" }
                    );
                markerRefs.current[clusterKey] = marker;
                return;
            }

            // Single asset
            const asset = entry.asset;
            if (asset.geometry.type === "Point") {
                const coords = asset.geometry.coordinates as number[];
                const position: [number, number] = [coords[1], coords[0]];
                const assetId = getAssetId(asset);
                const isSelected = selectedAsset
                    ? getAssetId(selectedAsset) === assetId
                    : false;

                // Create popup content
                const hash = Array.from(assetId).reduce(
                    (h, c) => (h * 31 + c.charCodeAt(0)) | 0,
                    0
                );
                const isOnline = Math.abs(hash) % 100 > 10; // ~90% online
                const popupContent = `
                    <div class="font-semibold text-slate-900">${
                        asset.feature_type
                    }</div>
                    <div class="text-xs text-slate-500">${
                        asset.feature_code
                    }</div>
                    <div class="mt-2 text-xs">
                        <span class="px-2 py-0.5 rounded-full ${
                            isOnline
                                ? "bg-green-100 text-green-700"
                                : "bg-red-100 text-red-700"
                        }">
                            ${isOnline ? "Trực tuyến" : "Ngoại tuyến"}
                        </span>
                    </div>
                `;

                const marker = L.marker(position, {
                    icon: getIconForAsset(asset.feature_code, isSelected),
                    zIndexOffset: isSelected ? 1000 : 0,
                })
                    .addTo(map)
                    .bindPopup(popupContent, {
                        className: "custom-popup",
                    })
                    .on("click", () => {
                        onAssetSelect(asset);
                    });

                markerRefs.current[assetId] = marker;
            }
        });

        // Add LineString polylines
        visibleAssets.forEach((asset) => {
            if (asset.geometry.type === "LineString") {
                const positions = (
                    asset.geometry.coordinates as number[][]
                ).map(
                    (coord: number[]) =>
                        [coord[1], coord[0]] as [number, number]
                );
                const color = getColorForFeatureCode(asset.feature_code);
                const assetId = getAssetId(asset);

                const popupContent = `
                    <div class="font-semibold text-slate-900">${asset.feature_type}</div>
                    <div class="text-xs text-slate-500">${asset.feature_code}</div>
                `;

                const polyline = L.polyline(positions, {
                    color,
                    weight: 4,
                    opacity: 0.8,
                })
                    .addTo(map)
                    .bindPopup(popupContent, {
                        className: "custom-popup",
                    })
                    .on("click", () => {
                        onAssetSelect(asset);
                    });

                polylineRefs.current[assetId] = polyline;
            }
        });
    }, [visibleAssets, mapMode, mapZoom, selectedAsset, onAssetSelect]);

    // Render route polyline
    useEffect(() => {
        if (!mapRef.current || !routePoints || routePoints.length <= 1) {
            if (routePolylineRef.current) {
                mapRef.current?.removeLayer(routePolylineRef.current);
                routePolylineRef.current = null;
            }
            return;
        }

        const map = mapRef.current;
        const positions = routePoints
            .filter((a) => a.geometry.type === "Point")
            .map((a) => {
                const coords = a.geometry.coordinates as number[];
                return [coords[1], coords[0]] as [number, number];
            });

        if (routePolylineRef.current) {
            map.removeLayer(routePolylineRef.current);
        }

        const routePolyline = L.polyline(positions, {
            color: "blue",
            weight: 4,
            opacity: 0.7,
            dashArray: "10, 10",
        }).addTo(map);

        routePolylineRef.current = routePolyline;
    }, [routePoints]);

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
            <div className="absolute top-4 right-4 z-51 bg-white rounded-lg shadow-md border border-slate-200 p-1 flex flex-col gap-1">
                <button
                    onClick={() => setMapMode("markers")}
                    className={`p-2 rounded hover:bg-slate-100 ${
                        mapMode === "markers"
                            ? "bg-blue-50 text-blue-600"
                            : "text-slate-600"
                    }`}
                    title="Chế độ điểm"
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
                    className={`p-2 rounded hover:bg-slate-100 ${
                        mapMode === "heatmap"
                            ? "bg-blue-50 text-blue-600"
                            : "text-slate-600"
                    }`}
                    title="Bản đồ nhiệt"
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

            {/* Map Container */}
            <div
                ref={containerRef}
                className="h-full w-full rounded-xl shadow-sm border border-slate-200"
            />

            {/* Heatmap Layer */}
            {mapMode === "heatmap" && mapRef.current && (
                <HeatmapLayer map={mapRef.current} points={heatmapPoints} />
            )}
        </div>
    );
};

export default MapComponent;
