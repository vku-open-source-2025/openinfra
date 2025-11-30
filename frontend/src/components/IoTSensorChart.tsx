import { useState, useMemo } from 'react';
import { useSensorData } from '../hooks/useIoT';
import type { IoTAlert } from '../hooks/useIoT';

interface IoTSensorChartProps {
    assetId: string | null;
    assetName?: string;
}

// Simple SVG line chart component
const LineChart = ({ 
    data, 
    width = 600, 
    height = 200, 
    color = '#3B82F6',
    thresholds
}: { 
    data: { time: string; value: number }[]; 
    width?: number; 
    height?: number;
    color?: string;
    thresholds?: { max?: number; critical_max?: number };
}) => {
    if (data.length === 0) return <div className="text-gray-400 text-center py-8">No data available</div>;

    const padding = { top: 20, right: 20, bottom: 30, left: 50 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;

    const values = data.map(d => d.value);
    const minValue = Math.min(...values, 0);
    const maxValue = Math.max(...values, thresholds?.critical_max || 0) * 1.1;

    const xScale = (index: number) => padding.left + (index / (data.length - 1)) * chartWidth;
    const yScale = (value: number) => padding.top + chartHeight - ((value - minValue) / (maxValue - minValue)) * chartHeight;

    const pathD = data
        .map((d, i) => `${i === 0 ? 'M' : 'L'} ${xScale(i)} ${yScale(d.value)}`)
        .join(' ');

    return (
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto">
            {/* Grid lines */}
            {[0, 0.25, 0.5, 0.75, 1].map(ratio => (
                <g key={ratio}>
                    <line
                        x1={padding.left}
                        y1={padding.top + chartHeight * ratio}
                        x2={width - padding.right}
                        y2={padding.top + chartHeight * ratio}
                        stroke="#374151"
                        strokeWidth={1}
                    />
                    <text
                        x={padding.left - 5}
                        y={padding.top + chartHeight * ratio + 4}
                        textAnchor="end"
                        className="text-xs fill-gray-400"
                    >
                        {(maxValue - (maxValue - minValue) * ratio).toFixed(1)}
                    </text>
                </g>
            ))}

            {/* Threshold lines */}
            {thresholds?.max && (
                <line
                    x1={padding.left}
                    y1={yScale(thresholds.max)}
                    x2={width - padding.right}
                    y2={yScale(thresholds.max)}
                    stroke="#F59E0B"
                    strokeWidth={2}
                    strokeDasharray="5,5"
                />
            )}
            {thresholds?.critical_max && (
                <line
                    x1={padding.left}
                    y1={yScale(thresholds.critical_max)}
                    x2={width - padding.right}
                    y2={yScale(thresholds.critical_max)}
                    stroke="#EF4444"
                    strokeWidth={2}
                    strokeDasharray="5,5"
                />
            )}

            {/* Data line */}
            <path
                d={pathD}
                fill="none"
                stroke={color}
                strokeWidth={2}
            />

            {/* Data points */}
            {data.map((d, i) => (
                <circle
                    key={i}
                    cx={xScale(i)}
                    cy={yScale(d.value)}
                    r={3}
                    fill={color}
                    className="hover:r-5 transition-all"
                >
                    <title>{`${d.time}: ${d.value.toFixed(2)}m`}</title>
                </circle>
            ))}

            {/* X-axis labels */}
            {data.filter((_, i) => i % Math.ceil(data.length / 6) === 0).map((d, i) => (
                <text
                    key={i}
                    x={xScale(i * Math.ceil(data.length / 6))}
                    y={height - 10}
                    textAnchor="middle"
                    className="text-xs fill-gray-400"
                >
                    {new Date(d.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </text>
            ))}
        </svg>
    );
};

// Alert badge component
const AlertBadge = ({ alert, onAcknowledge }: { alert: IoTAlert; onAcknowledge?: () => void }) => {
    const severityColors = {
        info: 'bg-blue-500/20 text-blue-400 border-blue-500/50',
        warning: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50',
        critical: 'bg-red-500/20 text-red-400 border-red-500/50'
    };

    return (
        <div className={`p-3 rounded-lg border ${severityColors[alert.severity]} flex justify-between items-start`}>
            <div>
                <div className="font-medium">{alert.message}</div>
                <div className="text-xs opacity-70 mt-1">
                    {new Date(alert.created_at).toLocaleString()}
                </div>
            </div>
            {onAcknowledge && (
                <button
                    onClick={onAcknowledge}
                    className="text-xs px-2 py-1 bg-white/10 rounded hover:bg-white/20 transition"
                >
                    Acknowledge
                </button>
            )}
        </div>
    );
};

// Stat card component
const StatCard = ({ label, value, unit, status }: { label: string; value: string | number; unit?: string; status?: 'normal' | 'warning' | 'critical' }) => {
    const statusColors = {
        normal: 'text-green-400',
        warning: 'text-yellow-400',
        critical: 'text-red-400'
    };

    return (
        <div className="bg-gray-800 rounded-lg p-4">
            <div className="text-xs text-gray-400 uppercase tracking-wider">{label}</div>
            <div className={`text-2xl font-bold mt-1 ${status ? statusColors[status] : 'text-white'}`}>
                {value}{unit && <span className="text-sm text-gray-400 ml-1">{unit}</span>}
            </div>
        </div>
    );
};

export default function IoTSensorChart({ assetId, assetName }: IoTSensorChartProps) {
    const { data, loading, error, refetch } = useSensorData(assetId, 60000);
    const [selectedMetric, setSelectedMetric] = useState<'water_level' | 'flow_rate'>('water_level');

    // Process readings for chart
    const chartData = useMemo(() => {
        if (!data?.readings) return [];
        
        return data.readings
            .filter(r => r.readings[selectedMetric] !== undefined)
            .slice(0, 100) // Last 100 readings
            .reverse()
            .map(r => ({
                time: r.timestamp,
                value: r.readings[selectedMetric] || 0
            }));
    }, [data?.readings, selectedMetric]);

    // Get latest reading
    const latestReading = useMemo(() => {
        if (!data?.readings?.length) return null;
        return data.readings[0];
    }, [data?.readings]);

    // Get thresholds from sensor config
    const thresholds = useMemo(() => {
        if (!data?.sensors?.length) return undefined;
        return data.sensors[0]?.config?.thresholds;
    }, [data?.sensors]);

    // Determine status based on thresholds
    const getValueStatus = (value: number | undefined): 'normal' | 'warning' | 'critical' => {
        if (value === undefined || !thresholds) return 'normal';
        if (thresholds.critical_max && value >= thresholds.critical_max) return 'critical';
        if (thresholds.max && value >= thresholds.max) return 'warning';
        return 'normal';
    };

    if (!assetId) {
        return (
            <div className="bg-gray-900 rounded-xl p-6 text-center text-gray-400">
                <div className="text-4xl mb-2">📡</div>
                <div>Select a drainage asset on the map to view IoT sensor data</div>
            </div>
        );
    }

    if (loading && !data) {
        return (
            <div className="bg-gray-900 rounded-xl p-6">
                <div className="animate-pulse space-y-4">
                    <div className="h-4 bg-gray-700 rounded w-1/3"></div>
                    <div className="h-48 bg-gray-700 rounded"></div>
                    <div className="grid grid-cols-3 gap-4">
                        <div className="h-20 bg-gray-700 rounded"></div>
                        <div className="h-20 bg-gray-700 rounded"></div>
                        <div className="h-20 bg-gray-700 rounded"></div>
                    </div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-gray-900 rounded-xl p-6">
                <div className="text-red-400 text-center">
                    <div className="text-4xl mb-2">⚠️</div>
                    <div>{error}</div>
                    <button 
                        onClick={refetch}
                        className="mt-4 px-4 py-2 bg-blue-600 rounded hover:bg-blue-700 transition"
                    >
                        Retry
                    </button>
                </div>
            </div>
        );
    }

    if (!data || data.summary.total_sensors === 0) {
        return (
            <div className="bg-gray-900 rounded-xl p-6 text-center text-gray-400">
                <div className="text-4xl mb-2">📡</div>
                <div>No IoT sensors configured for this asset</div>
            </div>
        );
    }

    return (
        <div className="bg-gray-900 rounded-xl p-6 space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h3 className="text-lg font-semibold text-white">
                        IoT Sensor Data
                    </h3>
                    <p className="text-sm text-gray-400">
                        {assetName || data.asset.feature_type} • {data.sensors[0]?.sensor_id}
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${data.sensors[0]?.status === 'active' ? 'bg-green-500' : 'bg-red-500'}`}></span>
                    <span className="text-sm text-gray-400">
                        {data.sensors[0]?.status === 'active' ? 'Online' : 'Offline'}
                    </span>
                </div>
            </div>

            {/* Metric selector */}
            <div className="flex gap-2">
                <button
                    onClick={() => setSelectedMetric('water_level')}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                        selectedMetric === 'water_level' 
                            ? 'bg-blue-600 text-white' 
                            : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                    }`}
                >
                    Water Level
                </button>
                <button
                    onClick={() => setSelectedMetric('flow_rate')}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                        selectedMetric === 'flow_rate' 
                            ? 'bg-blue-600 text-white' 
                            : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                    }`}
                >
                    Flow Rate
                </button>
            </div>

            {/* Chart */}
            <div className="bg-gray-800/50 rounded-lg p-4">
                <div className="text-sm text-gray-400 mb-2">
                    {selectedMetric === 'water_level' ? 'Water Level (m)' : 'Flow Rate (m³/s)'} - Last 24 Hours
                </div>
                <LineChart 
                    data={chartData} 
                    color={selectedMetric === 'water_level' ? '#3B82F6' : '#10B981'}
                    thresholds={selectedMetric === 'water_level' ? thresholds : undefined}
                />
                {thresholds && selectedMetric === 'water_level' && (
                    <div className="flex gap-4 mt-2 text-xs">
                        <span className="flex items-center gap-1">
                            <span className="w-3 h-0.5 bg-yellow-500"></span>
                            Warning: {thresholds.max}m
                        </span>
                        <span className="flex items-center gap-1">
                            <span className="w-3 h-0.5 bg-red-500"></span>
                            Critical: {thresholds.critical_max}m
                        </span>
                    </div>
                )}
            </div>

            {/* Stats grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatCard 
                    label="Current Level" 
                    value={latestReading?.readings.water_level?.toFixed(2) || '--'} 
                    unit="m"
                    status={getValueStatus(latestReading?.readings.water_level)}
                />
                <StatCard 
                    label="Flow Rate" 
                    value={latestReading?.readings.flow_rate?.toFixed(2) || '--'} 
                    unit="m³/s"
                />
                <StatCard 
                    label="Battery" 
                    value={latestReading?.battery || '--'} 
                    unit="%"
                    status={latestReading?.battery && latestReading.battery < 20 ? 'warning' : 'normal'}
                />
                <StatCard 
                    label="Signal" 
                    value={latestReading?.rssi || '--'} 
                    unit="dBm"
                />
            </div>

            {/* Alerts */}
            {data.alerts.length > 0 && (
                <div className="space-y-2">
                    <h4 className="text-sm font-medium text-gray-300">Active Alerts</h4>
                    {data.alerts.slice(0, 3).map(alert => (
                        <AlertBadge key={alert._id} alert={alert} />
                    ))}
                </div>
            )}

            {/* Last updated */}
            <div className="text-xs text-gray-500 text-right">
                Last reading: {latestReading ? new Date(latestReading.timestamp).toLocaleString() : 'N/A'}
                <button onClick={refetch} className="ml-2 text-blue-400 hover:underline">
                    Refresh
                </button>
            </div>
        </div>
    );
}
