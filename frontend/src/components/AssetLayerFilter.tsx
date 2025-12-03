import React, { useState, useMemo, useEffect } from 'react';
import { Zap, BatteryCharging, UtilityPole, TrafficCone, Lightbulb, Droplet, Waves, Activity, Filter, X } from 'lucide-react';
import type { Asset } from '../api';

// Feature code labels mapping
const featureCodeLabels: Record<string, string> = {
    'tram_dien': 'Trạm Điện',
    'tram_sac': 'Trạm Sạc',
    'cot_dien': 'Cột Điện',
    'den_giao_thong': 'Đèn Giao Thông',
    'den_duong': 'Đèn Đường',
    'tru_chua_chay': 'Trụ Chữa Cháy',
    'cong_thoat_nuoc': 'Cống Thoát Nước',
    'duong_ong_dien': 'Đường Ống Điện',
};

const featureCodeIcons: Record<string, React.ElementType> = {
    'tram_dien': Zap,
    'tram_sac': BatteryCharging,
    'cot_dien': UtilityPole,
    'den_giao_thong': TrafficCone,
    'den_duong': Lightbulb,
    'tru_chua_chay': Droplet,
    'cong_thoat_nuoc': Waves,
    'duong_ong_dien': Activity,
};

const featureCodeColors: Record<string, string> = {
    'tram_dien': '#fbbf24',
    'tram_sac': '#10b981',
    'cot_dien': '#64748b',
    'den_giao_thong': '#ef4444',
    'den_duong': '#f97316',
    'tru_chua_chay': '#3b82f6',
    'cong_thoat_nuoc': '#06b6d4',
    'duong_ong_dien': '#8b5cf6',
};

interface AssetLayerFilterProps {
    assets: Asset[];
    onFilterChange: (filteredAssets: Asset[]) => void;
}

const AssetLayerFilter: React.FC<AssetLayerFilterProps> = ({ assets, onFilterChange }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [selectedLayers, setSelectedLayers] = useState<Set<string>>(new Set());

    // Get all unique feature codes from assets
    const availableFeatureCodes = useMemo(() => {
        const codes = new Set<string>();
        assets.forEach(asset => {
            if (asset.feature_code) {
                codes.add(asset.feature_code);
            }
        });
        return Array.from(codes).sort();
    }, [assets]);

    // Initialize with all layers selected
    useEffect(() => {
        if (selectedLayers.size === 0 && availableFeatureCodes.length > 0) {
            setSelectedLayers(new Set(availableFeatureCodes));
        }
    }, [availableFeatureCodes, selectedLayers.size]);

    // Filter assets based on selected layers
    useEffect(() => {
        if (selectedLayers.size === 0) {
            onFilterChange([]);
            return;
        }

        const filtered = assets.filter(asset =>
            selectedLayers.has(asset.feature_code)
        );
        onFilterChange(filtered);
    }, [selectedLayers, assets, onFilterChange]);

    const toggleLayer = (featureCode: string) => {
        setSelectedLayers(prev => {
            const newSet = new Set(prev);
            if (newSet.has(featureCode)) {
                newSet.delete(featureCode);
            } else {
                newSet.add(featureCode);
            }
            return newSet;
        });
    };

    const selectAll = () => {
        setSelectedLayers(new Set(availableFeatureCodes));
    };

    const deselectAll = () => {
        setSelectedLayers(new Set());
    };

    const getAssetCount = (featureCode: string) => {
        return assets.filter(asset => asset.feature_code === featureCode).length;
    };

    return (
        <div className="absolute top-4 left-4 z-[1000]">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="bg-white rounded-lg shadow-lg border border-slate-200 p-3 hover:bg-slate-50 transition-colors flex items-center gap-2"
                title="Filter Asset Layers"
            >
                <Filter size={20} className="text-slate-700" />
                <span className="text-sm font-medium text-slate-700 hidden sm:inline">
                    Layers
                </span>
                {selectedLayers.size < availableFeatureCodes.length && (
                    <span className="bg-blue-500 text-white text-xs rounded-full px-2 py-0.5">
                        {selectedLayers.size}/{availableFeatureCodes.length}
                    </span>
                )}
            </button>

            {isOpen && (
                <div className="absolute top-full left-0 mt-2 w-72 bg-white rounded-lg shadow-xl border border-slate-200 overflow-hidden">
                    <div className="p-4 border-b border-slate-200 flex items-center justify-between">
                        <h3 className="font-semibold text-slate-900 flex items-center gap-2">
                            <Filter size={18} />
                            Asset Layers
                        </h3>
                        <button
                            onClick={() => setIsOpen(false)}
                            className="text-slate-400 hover:text-slate-600 transition-colors"
                        >
                            <X size={18} />
                        </button>
                    </div>

                    <div className="p-2 flex gap-2 border-b border-slate-200">
                        <button
                            onClick={selectAll}
                            className="flex-1 text-xs px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-md font-medium transition-colors"
                        >
                            Select All
                        </button>
                        <button
                            onClick={deselectAll}
                            className="flex-1 text-xs px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-md font-medium transition-colors"
                        >
                            Deselect All
                        </button>
                    </div>

                    <div className="max-h-96 overflow-y-auto p-2">
                        {availableFeatureCodes.length === 0 ? (
                            <div className="text-center py-8 text-slate-500 text-sm">
                                No asset layers available
                            </div>
                        ) : (
                            <div className="space-y-1">
                                {availableFeatureCodes.map((featureCode) => {
                                    const IconComponent = featureCodeIcons[featureCode] || Activity;
                                    const color = featureCodeColors[featureCode] || '#94a3b8';
                                    const label = featureCodeLabels[featureCode] || featureCode;
                                    const isSelected = selectedLayers.has(featureCode);
                                    const count = getAssetCount(featureCode);

                                    return (
                                        <button
                                            key={featureCode}
                                            onClick={() => toggleLayer(featureCode)}
                                            className={`w-full flex items-center gap-3 p-2.5 rounded-lg transition-colors text-left ${
                                                isSelected
                                                    ? 'bg-slate-50 hover:bg-slate-100'
                                                    : 'hover:bg-slate-50 opacity-60'
                                            }`}
                                        >
                                            <div
                                                className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
                                                style={{
                                                    backgroundColor: isSelected ? color : '#e2e8f0',
                                                    color: isSelected ? '#ffffff' : '#94a3b8',
                                                }}
                                            >
                                                <IconComponent size={16} />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <div className="text-sm font-medium text-slate-900">
                                                    {label}
                                                </div>
                                                <div className="text-xs text-slate-500">
                                                    {count} {count === 1 ? 'asset' : 'assets'}
                                                </div>
                                            </div>
                                            <div className="flex-shrink-0">
                                                <div
                                                    className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                                                        isSelected
                                                            ? 'bg-blue-500 border-blue-500'
                                                            : 'border-slate-300 bg-white'
                                                    }`}
                                                >
                                                    {isSelected && (
                                                        <svg
                                                            className="w-3 h-3 text-white"
                                                            fill="none"
                                                            viewBox="0 0 24 24"
                                                            stroke="currentColor"
                                                        >
                                                            <path
                                                                strokeLinecap="round"
                                                                strokeLinejoin="round"
                                                                strokeWidth={3}
                                                                d="M5 13l4 4L19 7"
                                                            />
                                                        </svg>
                                                    )}
                                                </div>
                                            </div>
                                        </button>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default AssetLayerFilter;
