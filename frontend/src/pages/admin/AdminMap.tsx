import React, { useState, useEffect, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate, useSearch } from "@tanstack/react-router";
import { getAssets, getAssetId, type Asset } from "../../api";
import MapComponent from "../../components/Map";
import AssetTable from "../../components/AssetTable";
import MaintenanceLogList from "../../components/MaintenanceLog";
import { useIoT } from "../../hooks/useIoT";
import {
    AlertTriangle,
    Activity,
    QrCode,
    Radio,
    ChevronDown,
    ChevronUp,
} from "lucide-react";
import QRCodeModal from "../../components/QRCodeModal";
import NFCWriteModal from "../../components/NFCWriteModal";

// Extended Asset type with status added by useIoT hook
type AssetWithStatus = Asset & {
    status?: "Online" | "Offline";
    lastPing?: string;
};

const AdminMap: React.FC = () => {
    const navigate = useNavigate();
    const searchParams = useSearch({ from: "/admin/map" }) as {
        assetId?: string;
    };
    const {
        data: initialAssets,
        isLoading,
        error,
    } = useQuery({
        queryKey: ["assets"],
        queryFn: getAssets,
    });

    const { assetsWithStatus, alerts } = useIoT(initialAssets);
    const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
    const [filteredAssets, setFilteredAssets] = useState<Asset[] | null>(null);
    const [routePoints, setRoutePoints] = useState<Asset[]>([]);

    const [showQRModal, setShowQRModal] = useState(false);
    const [showNFCModal, setShowNFCModal] = useState(false);
    const [assetTableCollapsed, setAssetTableCollapsed] = useState(false);
    const [detailsPanelCollapsed, setDetailsPanelCollapsed] = useState(false);

    // Use filtered assets if available, otherwise use live IoT assets
    const displayAssets = useMemo(() => {
        return filteredAssets || assetsWithStatus || [];
    }, [filteredAssets, assetsWithStatus]);

    // Sync URL param with selected asset
    useEffect(() => {
        const assetId = searchParams?.assetId;
        if (assetId && displayAssets.length > 0) {
            const asset = displayAssets.find((a) => getAssetId(a) === assetId);
            if (asset && (!selectedAsset || getAssetId(selectedAsset) !== getAssetId(asset))) {
                // Use setTimeout to avoid synchronous setState in effect
                setTimeout(() => {
                    setSelectedAsset(asset);
                }, 0);
            }
        }
    }, [searchParams, displayAssets, selectedAsset]);

    const handleAssetSelect = (asset: Asset | null) => {
        setSelectedAsset(asset);
        if (asset) {
            navigate({ to: "/admin/map", search: { assetId: getAssetId(asset) } });
        } else {
            navigate({
                to: "/admin/map",
                search: { assetId: undefined },
            });
        }
    };

    const handleRouteOptimization = () => {
        if (!displayAssets.length) return;

        const points = [...displayAssets]
            .filter((a) => a.geometry.type === "Point")
            .slice(0, 5)
            .sort(
                (a, b) => b.geometry.coordinates[1] - a.geometry.coordinates[1]
            );

        setRoutePoints(points);
        alert(`Route optimized for ${points.length} stops!`);
    };

    if (isLoading)
        return (
            <div className="flex h-full items-center justify-center bg-slate-50">
                <div className="text-center">
                    <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-slate-500 font-medium">
                        Loading system resources...
                    </p>
                </div>
            </div>
        );

    if (error)
        return (
            <div className="p-8 text-center text-red-500">
                Error loading assets
            </div>
        );

    return (
        <div className="flex flex-col h-full bg-slate-50 font-sans text-slate-900 overflow-hidden">
            <main className="flex-1 flex flex-col relative h-full">
                {/* Full Screen Map */}
                <div className="absolute inset-0 z-0">
                    <MapComponent
                        assets={displayAssets}
                        onAssetSelect={handleAssetSelect}
                        routePoints={routePoints}
                        selectedAsset={selectedAsset}
                        className="h-full w-full"
                    />
                </div>

                {/* Alert Feed Overlay */}
                {alerts.length > 0 && (
                    <div className="absolute top-4 right-4 z-50 w-80 pointer-events-none">
                        {alerts.map((alert, idx) => (
                            <div
                                key={idx}
                                className="bg-red-50 border-l-4 border-red-500 p-3 mb-2 shadow-lg rounded-r animate-in slide-in-from-right fade-in duration-300 pointer-events-auto flex items-start gap-3"
                            >
                                <AlertTriangle
                                    className="text-red-500 shrink-0"
                                    size={18}
                                />
                                <p className="text-xs font-medium text-red-800">
                                    {alert}
                                </p>
                            </div>
                        ))}
                    </div>
                )}

                {/* Floating Asset Table Panel - Bottom Left */}
                <div
                    className={`absolute bottom-4 left-4 z-10 w-full max-w-md bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden flex flex-col transition-all duration-300 ${
                        assetTableCollapsed ? "max-h-12" : "max-h-[50vh]"
                    }`}
                >
                    <div
                        className="px-6 py-3 border-b border-slate-100 flex justify-between items-center shrink-0 cursor-pointer hover:bg-slate-50 transition-colors"
                        onClick={() => {
                            if (assetTableCollapsed) {
                                setAssetTableCollapsed(false);
                            }
                        }}
                    >
                        <h3 className="font-bold text-lg">
                            {filteredAssets
                                ? `Filtered Assets (${filteredAssets.length})`
                                : "System Assets"}
                        </h3>
                        <div className="flex gap-2 items-center">
                            {!assetTableCollapsed && (
                                <>
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleRouteOptimization();
                                        }}
                                        className="text-xs bg-blue-50 text-blue-600 px-3 py-1 rounded-full font-medium hover:bg-blue-100 transition-colors flex items-center gap-1"
                                    >
                                        <Activity size={12} />
                                        Optimize Route
                                    </button>
                                    {filteredAssets && (
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setFilteredAssets(null);
                                            }}
                                            className="text-xs text-red-600 font-medium hover:text-red-800"
                                        >
                                            Clear Filter
                                        </button>
                                    )}
                                </>
                            )}
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setAssetTableCollapsed(
                                        !assetTableCollapsed
                                    );
                                }}
                                className="p-1 hover:bg-slate-200 rounded transition-colors"
                                title={
                                    assetTableCollapsed ? "Expand" : "Collapse"
                                }
                            >
                                {assetTableCollapsed ? (
                                    <ChevronUp size={18} />
                                ) : (
                                    <ChevronDown size={18} />
                                )}
                            </button>
                        </div>
                    </div>
                    {!assetTableCollapsed && (
                        <div className="flex-1 overflow-y-auto">
                            <AssetTable
                                assets={displayAssets}
                                onAssetSelect={handleAssetSelect}
                                selectedAssetId={selectedAsset ? getAssetId(selectedAsset) : undefined}
                            />
                        </div>
                    )}
                </div>

                {/* Floating Details Panel - Right Side */}
                <div
                    className={`absolute top-4 right-4 z-10 w-full max-w-sm bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden flex flex-col transition-all duration-300 ${
                        detailsPanelCollapsed
                            ? "max-h-14"
                            : "max-h-[calc(100vh-8rem)]"
                    }`}
                >
                    {selectedAsset ? (
                        <>
                            <div
                                className="p-6 border-b border-slate-100 bg-slate-50 cursor-pointer hover:bg-slate-100 transition-colors"
                                onClick={() => {
                                    if (detailsPanelCollapsed) {
                                        setDetailsPanelCollapsed(false);
                                    }
                                }}
                            >
                                <div className="flex items-start justify-between gap-3 mb-1">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-3 mb-1 flex-wrap">
                                            <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-bold rounded uppercase tracking-wide">
                                                {selectedAsset.feature_code}
                                            </span>
                                            <span className="text-xs text-slate-400">
                                                ID:{" "}
                                                {getAssetId(selectedAsset).slice(-6)}
                                            </span>
                                            {(selectedAsset as AssetWithStatus)
                                                .status && (
                                                <span
                                                    className={`px-2 py-1 text-xs font-bold rounded uppercase tracking-wide ${
                                                        (
                                                            selectedAsset as AssetWithStatus
                                                        ).status === "Online"
                                                            ? "bg-green-100 text-green-700"
                                                            : "bg-red-100 text-red-700"
                                                    }`}
                                                >
                                                    {
                                                        (
                                                            selectedAsset as AssetWithStatus
                                                        ).status
                                                    }
                                                </span>
                                            )}
                                        </div>
                                        <h3 className="text-xl font-bold text-slate-900">
                                            {selectedAsset.feature_type}
                                        </h3>
                                    </div>
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            setDetailsPanelCollapsed(
                                                !detailsPanelCollapsed
                                            );
                                        }}
                                        className="p-1 hover:bg-slate-200 rounded transition-colors shrink-0"
                                        title={
                                            detailsPanelCollapsed
                                                ? "Expand"
                                                : "Collapse"
                                        }
                                    >
                                        {detailsPanelCollapsed ? (
                                            <ChevronDown size={18} />
                                        ) : (
                                            <ChevronUp size={18} />
                                        )}
                                    </button>
                                </div>
                            </div>

                            {!detailsPanelCollapsed && (
                                <div className="flex-1 overflow-y-auto p-6">
                                    <div className="space-y-6">
                                        <div>
                                            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                                                Location
                                            </h4>
                                            <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                                                {selectedAsset.geometry.type ===
                                                    "Point" &&
                                                Array.isArray(
                                                    selectedAsset.geometry
                                                        .coordinates
                                                ) &&
                                                selectedAsset.geometry
                                                    .coordinates.length >= 2 &&
                                                typeof selectedAsset.geometry
                                                    .coordinates[0] ===
                                                    "number" &&
                                                typeof selectedAsset.geometry
                                                    .coordinates[1] ===
                                                    "number" ? (
                                                    <div className="grid grid-cols-2 gap-4 text-sm">
                                                        <div>
                                                            <p className="text-slate-500 text-xs">
                                                                Latitude
                                                            </p>
                                                            <p className="font-mono font-medium">
                                                                {(
                                                                    selectedAsset
                                                                        .geometry
                                                                        .coordinates as number[]
                                                                )[1].toFixed(6)}
                                                            </p>
                                                        </div>
                                                        <div>
                                                            <p className="text-slate-500 text-xs">
                                                                Longitude
                                                            </p>
                                                            <p className="font-mono font-medium">
                                                                {(
                                                                    selectedAsset
                                                                        .geometry
                                                                        .coordinates as number[]
                                                                )[0].toFixed(6)}
                                                            </p>
                                                        </div>
                                                    </div>
                                                ) : (
                                                    <div className="text-sm">
                                                        <p className="text-slate-500 text-xs mb-1">
                                                            Geometry Type
                                                        </p>
                                                        <p className="font-mono font-medium mb-2">
                                                            {
                                                                selectedAsset
                                                                    .geometry
                                                                    .type
                                                            }
                                                        </p>
                                                        <p className="text-slate-500 text-xs mb-1">
                                                            Details
                                                        </p>
                                                        <p className="font-mono font-medium">
                                                            {selectedAsset
                                                                .geometry
                                                                .type ===
                                                            "LineString"
                                                                ? `${selectedAsset.geometry.coordinates.length} points`
                                                                : "Complex Geometry"}
                                                        </p>
                                                    </div>
                                                )}
                                            </div>
                                        </div>

                                        <div>
                                            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                                                Maintenance History
                                            </h4>
                                            <MaintenanceLogList
                                                assetId={getAssetId(selectedAsset)}
                                            />
                                        </div>
                                    </div>
                                </div>
                            )}

                            {!detailsPanelCollapsed && (
                                <div className="p-4 border-t border-slate-100 bg-slate-50 flex gap-2">
                                    <button
                                        onClick={() => setShowQRModal(true)}
                                        className="flex-1 py-2 bg-white border border-slate-300 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 shadow-sm flex items-center justify-center gap-2"
                                    >
                                        <QrCode size={16} />
                                        QR Code
                                    </button>
                                    <button
                                        onClick={() => setShowNFCModal(true)}
                                        className="flex-1 py-2 bg-white border border-slate-300 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 shadow-sm flex items-center justify-center gap-2"
                                    >
                                        <Radio size={16} />
                                        Write NFC
                                    </button>
                                </div>
                            )}
                        </>
                    ) : (
                        <div className="h-full flex flex-col items-center justify-center text-center p-8 text-slate-400">
                            <div className="bg-slate-100 p-4 rounded-full mb-4">
                                <Activity
                                    size={32}
                                    className="text-slate-300"
                                />
                            </div>
                            <p className="font-medium text-slate-500">
                                No Asset Selected
                            </p>
                            <p className="text-sm mt-2">
                                Select an asset from the map or list to view
                                details.
                            </p>
                        </div>
                    )}
                </div>

                <QRCodeModal
                    isOpen={showQRModal}
                    onClose={() => setShowQRModal(false)}
                    asset={selectedAsset}
                />

                <NFCWriteModal
                    isOpen={showNFCModal}
                    onClose={() => setShowNFCModal(false)}
                    asset={selectedAsset}
                />
            </main>
        </div>
    );
};

export default AdminMap;
