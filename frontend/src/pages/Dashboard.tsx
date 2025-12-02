import React, { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { getAssets, type Asset } from "../api";
import MapComponent from "../components/Map";
import AssetTable from "../components/AssetTable";
import MaintenanceLogList from "../components/MaintenanceLog";
import Sidebar from "../components/Sidebar";
import StatsCard from "../components/StatsCard";
import CalendarView from "../components/CalendarView";
import { useIoT } from "../hooks/useIoT";
import QRCodeModal from "../components/QRCodeModal";
import NFCWriteModal from "../components/NFCWriteModal";
import { NotificationCenter } from "../components/notifications/NotificationCenter";
import IoTSensorChart from '../components/IoTSensorChart';
import {
    Zap,
    AlertTriangle,
    CheckCircle,
    Activity,
    QrCode,
    Radio,
} from "lucide-react";

const Dashboard: React.FC = () => {
    const [activeTab, setActiveTab] = useState("dashboard");
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

    // Use filtered assets if available, otherwise use live IoT assets
    const displayAssets = filteredAssets || assetsWithStatus || [];

    const handleRouteOptimization = () => {
        // Simple greedy routing: Sort by latitude (north to south) as a basic heuristic
        // In a real app, use OSRM or Google Directions API
        if (!displayAssets.length) return;

        const points = [...displayAssets]
            .filter((a) => a.geometry.type === "Point")
            .slice(0, 5) // Pick top 5 for demo
            .sort(
                (a, b) => b.geometry.coordinates[1] - a.geometry.coordinates[1]
            );

        setRoutePoints(points);
        alert(`Route optimized for ${points.length} stops!`);
    };

    // Fake logs for calendar
    const fakeCalendarLogs = useMemo(() => {
        if (!initialAssets) return [];
        const logs = [];
        const statuses = ["Pending", "In Progress", "Completed"];
        const now = new Date();

        for (let i = 0; i < 50; i++) {
            const date = new Date(now);
            date.setDate(date.getDate() + Math.floor(Math.random() * 60) - 30);
            logs.push({
                _id: `log-${i}`,
                scheduled_date: date.toISOString(),
                description: `Maintenance for ${
                    initialAssets[i % initialAssets.length]?.feature_code ||
                    "Asset"
                }`,
                status: statuses[Math.floor(Math.random() * statuses.length)],
            });
        }
        return logs;
    }, [initialAssets]);

    if (isLoading)
        return (
            <div className="flex h-screen items-center justify-center bg-slate-50">
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

    const assetCount = displayAssets.length;
    const activeAlerts = alerts.length + Math.floor(assetCount * 0.02);
    const maintenanceDue = Math.floor(assetCount * 0.12);
    const operationalRate = (
        ((assetCount - activeAlerts) / assetCount) *
        100
    ).toFixed(1);

    return (
        <div className="flex h-screen bg-slate-50 font-sans text-slate-900">
            {/* <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} /> */}

            <main className="flex-1 flex flex-col overflow-hidden relative">
                {/* Alert Feed Overlay */}
                {alerts.length > 0 && (
                    <div className="absolute top-20 right-8 z-50 w-80 pointer-events-none">
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

                <header className="bg-white border-b border-slate-200 px-8 py-4 flex justify-between items-center">
                    <div>
                        <h2 className="text-2xl font-bold text-slate-800">
                            {activeTab === "dashboard"
                                ? "Overview"
                                : activeTab === "map"
                                ? "Geospatial View"
                                : activeTab === "maintenance"
                                ? "Maintenance Schedule"
                                : "Analytics"}
                        </h2>
                        <p className="text-sm text-slate-500">
                            System status and asset performance
                        </p>
                    </div>
                    <div className="flex gap-3 items-center">
                        <NotificationCenter />
                        <button
                            onClick={handleRouteOptimization}
                            className="px-4 py-2 bg-white border border-slate-300 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 flex items-center gap-2"
                        >
                            <Activity size={16} />
                            Optimize Route
                        </button>
                        <button className="px-4 py-2 bg-blue-600 rounded-lg text-sm font-medium text-white hover:bg-blue-700 shadow-sm flex items-center gap-2">
                            <Zap size={16} />
                            Add Asset
                        </button>
                    </div>
                </header>

                <div className="flex-1 overflow-y-auto p-8">
                    {activeTab === "maintenance" ? (
                        <CalendarView logs={fakeCalendarLogs} />
                    ) : (
                        <>
                            {/* Stats Row */}
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                                <StatsCard
                                    title="Total Assets"
                                    value={assetCount}
                                    icon={Zap}
                                    color="bg-blue-500"
                                    trend="12%"
                                    trendUp={true}
                                />
                                <StatsCard
                                    title="Active Alerts"
                                    value={activeAlerts}
                                    icon={AlertTriangle}
                                    color="bg-red-500"
                                    trend="2"
                                    trendUp={false}
                                />
                                <StatsCard
                                    title="Maintenance Due"
                                    value={maintenanceDue}
                                    icon={Activity}
                                    color="bg-amber-500"
                                    trend="5%"
                                    trendUp={false}
                                />
                                <StatsCard
                                    title="Operational Rate"
                                    value={`${operationalRate}%`}
                                    icon={CheckCircle}
                                    color="bg-green-500"
                                    trend="0.5%"
                                    trendUp={true}
                                />
                            </div>

                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 h-[600px]">
                                {/* Left Column: Map & List */}
                                <div className="lg:col-span-2 flex flex-col gap-6 h-full overflow-hidden">
                                    <div className="bg-white p-1 rounded-xl shadow-sm border border-slate-200 h-[60%] shrink-0">
                                        <MapComponent
                                            assets={displayAssets}
                                            onAssetSelect={setSelectedAsset}
                                            onFilterByShape={setFilteredAssets}
                                            routePoints={routePoints}
                                            className="h-full"
                                        />
                                    </div>

                                    <div className="bg-white rounded-xl shadow-sm border border-slate-200 flex-1 overflow-hidden flex flex-col min-h-0">
                                        <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center">
                                            <h3 className="font-bold text-lg">
                                                {filteredAssets
                                                    ? `Filtered Assets (${filteredAssets.length})`
                                                    : "Recent Assets"}
                                            </h3>
                                            {filteredAssets && (
                                                <button
                                                    onClick={() =>
                                                        setFilteredAssets(null)
                                                    }
                                                    className="text-xs text-red-600 font-medium hover:text-red-800"
                                                >
                                                    Clear Filter
                                                </button>
                                            )}
                                        </div>
                                        <div className="flex-1 overflow-y-auto">
                                            <AssetTable
                                                assets={displayAssets}
                                                onAssetSelect={setSelectedAsset}
                                                selectedAssetId={
                                                    selectedAsset?._id
                                                }
                                            />
                                        </div>
                                    </div>
                                </div>

                                {/* Right Column: Details Panel */}
                                <div className="bg-white rounded-xl shadow-sm border border-slate-200 h-full overflow-hidden flex flex-col">
                                    {selectedAsset ? (
                                        <>
                                            <div className="p-6 border-b border-slate-100 bg-slate-50">
                                                <div className="flex items-center gap-3 mb-1">
                                                    <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-bold rounded uppercase tracking-wide">
                                                        {
                                                            selectedAsset.feature_code
                                                        }
                                                    </span>
                                                    <span className="text-xs text-slate-400">
                                                        ID:{" "}
                                                        {selectedAsset._id.slice(
                                                            -6
                                                        )}
                                                    </span>
                                                    {/* @ts-ignore */}
                                                    {selectedAsset.status && (
                                                        /* @ts-ignore */
                                                        <span
                                                            className={`px-2 py-1 text-xs font-bold rounded uppercase tracking-wide ${
                                                                selectedAsset.status ===
                                                                "Online"
                                                                    ? "bg-green-100 text-green-700"
                                                                    : "bg-red-100 text-red-700"
                                                            }`}
                                                        >
                                                            {/* @ts-ignore */}
                                                            {
                                                                selectedAsset.status
                                                            }
                                                        </span>
                                                    )}
                                                </div>
                                                <h3 className="text-xl font-bold text-slate-900">
                                                    {selectedAsset.feature_type}
                                                </h3>
                                            </div>

                                            <div className="flex-1 overflow-y-auto p-6">
                                                <div className="space-y-6">
                                                    <div>
                                                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                                                            Location
                                                        </h4>
                                                        <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                                                            {selectedAsset
                                                                .geometry
                                                                .type ===
                                                            "Point" ? (
                                                                <div className="grid grid-cols-2 gap-4 text-sm">
                                                                    <div>
                                                                        <p className="text-slate-500 text-xs">
                                                                            Latitude
                                                                        </p>
                                                                        <p className="font-mono font-medium">
                                                                            {selectedAsset.geometry.coordinates[1].toFixed(
                                                                                6
                                                                            )}
                                                                        </p>
                                                                    </div>
                                                                    <div>
                                                                        <p className="text-slate-500 text-xs">
                                                                            Longitude
                                                                        </p>
                                                                        <p className="font-mono font-medium">
                                                                            {selectedAsset.geometry.coordinates[0].toFixed(
                                                                                6
                                                                            )}
                                                                        </p>
                                                                    </div>
                                                                </div>
                                                            ) : (
                                                                <div className="text-sm">
                                                                    <p className="text-slate-500 text-xs mb-1">
                                                                        Geometry
                                                                        Type
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
                                                            assetId={
                                                                selectedAsset._id
                                                            }
                                                        />
                                                    </div>

                                                    {/* IoT Sensor Chart for drainage assets */}
                                                    {selectedAsset.feature_code === 'cong_thoat_nuoc' && (
                                                        <div>
                                                            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">IoT Sensor Data</h4>
                                                            <IoTSensorChart 
                                                                assetId={selectedAsset._id} 
                                                                assetName={selectedAsset.feature_type}
                                                            />
                                                        </div>
                                                    )}
                                                </div>
                                            </div>

                                            <div className="p-4 border-t border-slate-100 bg-slate-50 flex flex-col gap-2">
                                                <div className="flex gap-2">
                                                    <button
                                                        onClick={() =>
                                                            setShowQRModal(true)
                                                        }
                                                        className="flex-1 py-2 bg-white border border-slate-300 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 shadow-sm flex items-center justify-center gap-2"
                                                    >
                                                        <QrCode size={16} />
                                                        QR Code
                                                    </button>
                                                    <button
                                                        onClick={() =>
                                                            setShowNFCModal(
                                                                true
                                                            )
                                                        }
                                                        className="flex-1 py-2 bg-white border border-slate-300 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 shadow-sm flex items-center justify-center gap-2"
                                                    >
                                                        <Radio size={16} />
                                                        Write NFC
                                                    </button>
                                                </div>
                                                <button className="w-full py-2 bg-blue-600 border border-transparent rounded-lg text-sm font-medium text-white hover:bg-blue-700 shadow-sm">
                                                    Schedule Maintenance
                                                </button>
                                            </div>
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
                                                Select an asset from the map or
                                                list to view details and
                                                maintenance history.
                                            </p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </>
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

export default Dashboard;
