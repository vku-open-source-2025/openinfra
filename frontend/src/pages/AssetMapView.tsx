import React, {
    useState,
    useEffect,
    useMemo,
    useRef,
    useCallback,
} from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate, useSearch } from "@tanstack/react-router";
import L from "leaflet";
import { assetsApi } from "../api/assets";
import type { Asset } from "../types/asset";
import { getIconForAsset, getColorForFeatureCode } from "../utils/mapIcons";
import AssetLayerFilter from "../components/AssetLayerFilter";
import AssetInfoPanel from "../components/AssetInfoModal";
import AIChatWidget from "../components/AIChatWidget";
import "leaflet/dist/leaflet.css";

// Disable default Leaflet marker icons
// eslint-disable-next-line @typescript-eslint/no-explicit-any
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: undefined,
    iconUrl: undefined,
    shadowUrl: undefined,
});

// VietMap API key from environment
const VIETMAP_API_KEY = import.meta.env.VITE_VIETMAP_API_KEY || "";

const center: [number, number] = [16.047079, 108.20623];

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
            return (geometry.coordinates as number[][][])[0].map(toLatLng);
        case "MultiPolygon":
            return (geometry.coordinates as unknown as number[][][][]).flatMap(
                (poly) => poly[0].map(toLatLng)
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

const AssetMapView: React.FC = () => {
    const navigate = useNavigate();
    const searchParams = useSearch({ from: "/admin/map" }) as {
        assetId?: string;
    };

    const {
        data: assets,
        isLoading,
        error,
    } = useQuery({
        queryKey: ["assets"],
        queryFn: () => assetsApi.list(),
    });

    const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [filteredAssets, setFilteredAssets] = useState<Asset[]>([]);
    const [mapBounds, setMapBounds] = useState<L.LatLngBounds | null>(null);
    const [openChatbot, setOpenChatbot] = useState(false);
    const [assetToAddToChat, setAssetToAddToChat] = useState<Asset | null>(
        null
    );
    const mapRef = useRef<L.Map | null>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const markerRefs = useRef<{ [key: string]: L.Marker | null }>({});
    const polylineRefs = useRef<{ [key: string]: L.Polyline | null }>({});
    const tileLayerRef = useRef<L.TileLayer | null>(null);
    const hasInitializedAssets = useRef(false);
    const isUpdatingFromUrl = useRef(false);

    // Fetch full asset details when selected
    const { data: fullAssetDetails, isLoading: isLoadingAssetDetails } =
        useQuery({
            queryKey: [
                "asset",
                selectedAsset
                    ? (selectedAsset as any).id || (selectedAsset as any)._id
                    : null,
            ],
            queryFn: () => {
                const assetId =
                    (selectedAsset as any)?.id || (selectedAsset as any)?._id;
                return assetsApi.getById(assetId);
            },
            enabled: !!selectedAsset && isModalOpen,
        });

    // Initialize filtered assets with all assets
    useEffect(() => {
        if (assets && assets.length > 0 && !hasInitializedAssets.current) {
            // Use setTimeout to avoid synchronous setState in effect
            setTimeout(() => {
                setFilteredAssets(assets);
                hasInitializedAssets.current = true;
            }, 0);
        }
    }, [assets]);

    // Sync URL param with selected asset
    useEffect(() => {
        if (isUpdatingFromUrl.current) {
            isUpdatingFromUrl.current = false;
            return;
        }

        const assetId = searchParams?.assetId;
        const currentAssetId = selectedAsset
            ? (selectedAsset as any).id || (selectedAsset as any)._id
            : null;

        if (assetId && assets && assets.length > 0) {
            if (currentAssetId !== assetId) {
                const asset = assets.find(
                    (a) => ((a as any).id || (a as any)._id) === assetId
                );
                if (asset) {
                    // Use setTimeout to avoid synchronous setState in effect
                    setTimeout(() => {
                        setSelectedAsset(asset);
                        setIsModalOpen(true);
                    }, 0);
                }
            }
        } else if (!assetId && currentAssetId) {
            // URL param removed, close modal
            setTimeout(() => {
                setSelectedAsset(null);
                setIsModalOpen(false);
            }, 0);
        }
    }, [searchParams?.assetId, assets, selectedAsset]);

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

    const visibleAssets = useMemo(() => {
        if (!mapBounds) return filteredAssets;
        const filtered = filteredAssets.filter((asset) =>
            assetIntersectsBounds(asset, mapBounds)
        );

        // Always include selected asset even if currently out of bounds
        if (selectedAsset) {
            const selectedId =
                (selectedAsset as any).id || (selectedAsset as any)._id;
            if (
                !filtered.find(
                    (a) => ((a as any).id || (a as any)._id) === selectedId
                )
            ) {
                filtered.push(selectedAsset);
            }
        }

        return filtered;
    }, [filteredAssets, assetIntersectsBounds, mapBounds, selectedAsset]);

    const handleAssetClick = useCallback(
        (asset: Asset) => {
            const assetId = (asset as any).id || (asset as any)._id;
            isUpdatingFromUrl.current = true;
            setSelectedAsset(asset);
            setIsModalOpen(true);
            // Close chat panel when opening asset details
            setOpenChatbot(false);
            setAssetToAddToChat(null);
            navigate({ to: "/admin/map", search: { assetId } });
        },
        [navigate]
    );

    const handleModalClose = useCallback(() => {
        isUpdatingFromUrl.current = true;
        setIsModalOpen(false);
        setSelectedAsset(null);
        navigate({ to: "/admin/map", search: { assetId: undefined } });
    }, [navigate]);

    const handleViewDetails = useCallback(
        (assetId: string) => {
            navigate({ to: "/admin/assets/$id", params: { id: assetId } });
        },
        [navigate]
    );

    const handleAddToChat = useCallback(
        (asset: Asset) => {
            setAssetToAddToChat(asset);
            setOpenChatbot(true);
            // Close the asset info panel when adding to chat
            setIsModalOpen(false);
            setSelectedAsset(null);
            navigate({ to: "/admin/map", search: { assetId: undefined } });
        },
        [navigate]
    );

    // Memoize filter change handler to prevent infinite loops
    const handleFilterChange = useCallback(
        (filtered: import("../api").Asset[]) => {
            setFilteredAssets(filtered as unknown as Asset[]);
        },
        []
    );

    // Initialize map
    useEffect(() => {
        if (!containerRef.current || mapRef.current) return;

        const map = L.map(containerRef.current, {
            center,
            zoom: 16,
            maxZoom: 20,
            scrollWheelZoom: true,
        });

        // Add tile layer
        const tileLayer = VIETMAP_API_KEY
            ? L.tileLayer(
                  `https://maps.vietmap.vn/maps/tiles/tm/{z}/{x}/{y}@2x.png?apikey=${VIETMAP_API_KEY}`,
                  {
                      attribution:
                          '&copy; <a href="https://vietmap.vn">VietMap</a> | Hoang Sa and Truong Sa belong to Vietnam 🇻🇳',
                      maxZoom: 20,
                  }
              )
            : L.tileLayer(
                  "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                  {
                      attribution:
                          '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                      maxZoom: 20,
                      maxNativeZoom: 16,
                  }
              );

        tileLayer.addTo(map);
        tileLayerRef.current = tileLayer;
        mapRef.current = map;

        // Set initial bounds
        setMapBounds(map.getBounds());

        // Listen to map events for bounds updates
        const updateBounds = () => {
            setMapBounds(map.getBounds());
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
        const assetId = (selectedAsset as any).id || (selectedAsset as any)._id;

        if (selectedAsset.geometry.type === "Point") {
            const [lng, lat] = selectedAsset.geometry.coordinates as number[];

            map.flyTo([lat, lng], 18, {
                animate: true,
                duration: 1.5,
            });

            const marker = markerRefs.current[assetId];
            if (marker) {
                setTimeout(() => {
                    marker.openPopup();
                }, 500);
            }
            return;
        }

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
        if (!mapRef.current) return;

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

        // Add Point markers
        visibleAssets.forEach((asset) => {
            if (asset.geometry.type === "Point") {
                const coords = asset.geometry.coordinates as number[];
                const position: [number, number] = [coords[1], coords[0]];
                const assetId = (asset as any).id || (asset as any)._id;
                const isSelected =
                    selectedAsset &&
                    ((selectedAsset as any).id ||
                        (selectedAsset as any)._id) === assetId;

                const marker = L.marker(position, {
                    icon: getIconForAsset(asset.feature_code, !!isSelected),
                    zIndexOffset: isSelected ? 1000 : 0,
                })
                    .addTo(map)
                    .on("click", () => handleAssetClick(asset));

                markerRefs.current[assetId] = marker;
            }
        });

        // Add LineString polylines
        visibleAssets.forEach((asset) => {
            if (asset.geometry.type === "LineString") {
                const positions = (
                    asset.geometry.coordinates as number[][]
                ).map((coord: any) => [coord[1], coord[0]] as [number, number]);
                const color = getColorForFeatureCode(asset.feature_code);
                const assetId = (asset as any).id || (asset as any)._id;

                const polyline = L.polyline(positions, {
                    color,
                    weight: 4,
                    opacity: 0.8,
                })
                    .addTo(map)
                    .on("click", () => handleAssetClick(asset));

                polylineRefs.current[assetId] = polyline;
            }
        });
    }, [visibleAssets, selectedAsset, handleAssetClick]);

    if (error)
        return (
            <div className="flex h-full items-center justify-center bg-slate-50">
                <div className="text-center">
                    <p className="text-red-500 font-medium mb-2">
                        Lỗi khi tải danh sách tài sản
                    </p>
                    <p className="text-sm text-slate-500">
                        Vui lòng thử làm mới trang
                    </p>
                </div>
            </div>
        );

    return (
        <div className="relative w-full h-full min-h-0 bg-slate-50 overflow-hidden z-0">
            {/* Loading overlay */}
            {isLoading && (
                <div className="absolute inset-0 z-10 flex items-center justify-center bg-white/80 backdrop-blur-sm">
                    <div className="text-center">
                        <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                        <p className="text-slate-500 font-medium">
                            Đang tải danh sách tài sản...
                        </p>
                    </div>
                </div>
            )}
            {/* Asset Layer Filter */}
            {assets && assets.length > 0 && (
                <AssetLayerFilter
                    assets={assets as unknown as import("../api").Asset[]}
                    onFilterChange={handleFilterChange}
                />
            )}

            {/* Map Container */}
            <div ref={containerRef} className="h-full w-full z-0" />

            {/* Asset Info Panel */}
            <AssetInfoPanel
                asset={fullAssetDetails || selectedAsset}
                isOpen={isModalOpen}
                onClose={handleModalClose}
                onViewDetails={handleViewDetails}
                onAddToChat={handleAddToChat}
                isLoading={isLoadingAssetDetails}
            />

            {/* AI Chatbot Widget */}
            <AIChatWidget
                openChat={openChatbot}
                onOpenChange={(isOpen) => {
                    setOpenChatbot(isOpen);
                    if (isOpen) {
                        // Close asset details panel when opening chat
                        isUpdatingFromUrl.current = true;
                        setIsModalOpen(false);
                        setSelectedAsset(null);
                        navigate({
                            to: "/admin/map",
                            search: { assetId: undefined },
                        });
                    } else {
                        // Reset asset to add when closing
                        setAssetToAddToChat(null);
                    }
                }}
                addAssetToContext={assetToAddToChat}
            />
        </div>
    );
};

export default AssetMapView;
