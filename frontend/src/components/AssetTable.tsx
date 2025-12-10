import React from 'react';
import { useNavigate } from '@tanstack/react-router';
import { type Asset, getAssetId } from '../api';
import { ChevronRight } from 'lucide-react';

interface AssetTableProps {
    assets: Asset[];
    onAssetSelect?: (asset: Asset) => void;
    selectedAssetId?: string;
}

const AssetTable: React.FC<AssetTableProps> = ({ assets, onAssetSelect, selectedAssetId }) => {
    const navigate = useNavigate();

    const handleAssetClick = (asset: Asset) => {
        if (onAssetSelect) {
            onAssetSelect(asset);
        } else {
            // Navigate to asset detail page if no onAssetSelect handler
            navigate({ to: `/admin/assets/${getAssetId(asset)}` });
        }
    };

    return (
        <div className="overflow-hidden bg-white rounded-xl shadow-sm border border-slate-200">
            <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200">
                    <thead className="bg-slate-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Loại</th>
                            <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Mã</th>
                            <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Ngày tạo</th>
                            <th className="relative px-6 py-3"><span className="sr-only">Hành động</span></th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-slate-200">
                        {assets.map((asset) => {
                            const assetId = getAssetId(asset);
                            return (
                            <tr
                                key={assetId}
                                onClick={() => handleAssetClick(asset)}
                                className={`cursor-pointer transition-colors duration-150 ${selectedAssetId === assetId
                                        ? 'bg-blue-50 hover:bg-blue-100'
                                        : 'hover:bg-slate-50'
                                    }`}
                            >
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="flex items-center">
                                        <div className="text-sm font-medium text-slate-900">{asset.feature_type}</div>
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-slate-100 text-slate-800">
                                        {asset.feature_code}
                                    </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                                    {new Date(asset.created_at).toLocaleDateString("vi-VN")}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                    <ChevronRight size={16} className="text-slate-400" />
                                </td>
                            </tr>
                        );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default AssetTable;
