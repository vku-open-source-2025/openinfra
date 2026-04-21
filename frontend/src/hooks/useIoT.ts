import { useState, useEffect, useCallback, useMemo } from 'react';
import type { Asset } from '../api';
import { api } from '../api';

// Types for IoT data - matching actual API response
export interface Sensor {
    id: string;
    _id?: string;
    sensor_code: string;
    asset_id: string;
    sensor_type: string;
    manufacturer?: string;
    model?: string;
    measurement_unit?: string;
    status: string;
    thresholds?: {
        min_value?: number;
        max_value?: number;
        critical_min?: number;
        critical_max?: number;
        warning_min?: number;
        warning_max?: number;
    };
    // Legacy config format
    config?: {
        thresholds: {
            min: number;
            max: number;
            critical_min: number;
            critical_max: number;
        };
        sampling_interval: number;
    };
    last_seen?: string;
    last_reading?: number;
    created_at: string;
}

export interface SensorReading {
    id?: string;
    _id?: string;
    sensor_id: string;
    asset_id?: string;
    timestamp: string;
    value?: number;
    readings?: {
        water_level?: number;
        flow_rate?: number;
        [key: string]: number | undefined;
    };
    battery?: number;
    rssi?: number;
    metadata?: Record<string, unknown>;
}

export interface IoTAlert {
    _id: string;
    sensor_id: string;
    asset_id: string;
    alert_type: string;
    severity: 'info' | 'warning' | 'critical';
    message: string;
    value: number;
    threshold: number;
    created_at: string;
    acknowledged: boolean;
}

export interface AssetIoTData {
    asset_id: string;
    asset: {
        id: string;
        feature_type: string;
        feature_code: string;
    };
    sensors: Sensor[];
    readings: SensorReading[];
    alerts: IoTAlert[];
    summary: {
        total_sensors: number;
        total_readings: number;
        active_alerts: number;
    };
}

type AssetWithIoTStatus = Omit<Asset, 'status'> & {
    status: 'Online' | 'Offline';
    lastPing: string;
};

const createInitialAssetStatuses = (assets: Asset[]): AssetWithIoTStatus[] => {
    return assets.map(asset => ({
        ...asset,
        status: Math.random() > 0.05 ? 'Online' : 'Offline',
        lastPing: new Date().toISOString()
    }));
};

const getErrorMessage = (error: unknown, fallback: string): string => {
    if (error instanceof Error && error.message) {
        return error.message;
    }
    return fallback;
};

// API functions
export const iotApi = {
    async getSensors(assetId?: string): Promise<Sensor[]> {
        const params = assetId ? `?asset_id=${assetId}` : '';
        const response = await api.get(`/iot/sensors${params}`);
        return response.data;
    },

    async getSensorReadings(sensorId: string, hours: number = 24): Promise<SensorReading[]> {
        const response = await api.get(`/iot/sensors/${sensorId}/readings?limit=${hours * 12}`);
        return response.data.readings;
    },

    async getAssetIoTData(assetId: string, hours: number = 24): Promise<AssetIoTData> {
        const response = await api.get(`/iot/assets/${assetId}/iot-data?hours=${hours}`);
        return response.data;
    },

    async getAlerts(acknowledged?: boolean): Promise<IoTAlert[]> {
        const params = acknowledged !== undefined ? `?acknowledged=${acknowledged}` : '';
        const response = await api.get(`/iot/alerts${params}`);
        return response.data;
    },

    async acknowledgeAlert(alertId: string): Promise<void> {
        await api.post(`/iot/alerts/${alertId}/acknowledge`);
    }
};

// Hook for legacy asset status simulation
export const useIoT = (initialAssets: Asset[] | undefined) => {
    const [assetsWithStatus, setAssetsWithStatus] = useState<AssetWithIoTStatus[]>([]);
    const [alerts, setAlerts] = useState<string[]>([]);

    const seededAssets = useMemo<AssetWithIoTStatus[]>(() => {
        if (!initialAssets || initialAssets.length === 0) {
            return [];
        }
        return createInitialAssetStatuses(initialAssets);
    }, [initialAssets]);

    const assetsInSync = useMemo(() => {
        if (!initialAssets) {
            return assetsWithStatus.length === 0;
        }
        if (assetsWithStatus.length !== initialAssets.length) {
            return false;
        }
        const currentIds = new Set(assetsWithStatus.map(asset => asset.id));
        return initialAssets.every(asset => currentIds.has(asset.id));
    }, [assetsWithStatus, initialAssets]);

    useEffect(() => {
        if (!initialAssets || initialAssets.length === 0) return;

        const seededById = new Map(seededAssets.map(asset => [asset.id, asset]));

        const interval = setInterval(() => {
            setAssetsWithStatus(current => {
                const currentById = new Map(current.map(asset => [asset.id, asset]));
                const next: AssetWithIoTStatus[] = initialAssets.map(asset => {
                    const existing = currentById.get(asset.id) ?? seededById.get(asset.id);
                    if (existing) {
                        return {
                            ...asset,
                            status: existing.status,
                            lastPing: existing.lastPing
                        };
                    }
                    return {
                        ...asset,
                        status: Math.random() > 0.05 ? 'Online' : 'Offline',
                        lastPing: new Date().toISOString()
                    };
                });

                if (next.length === 0) {
                    return [];
                }

                const numUpdates = Math.floor(Math.random() * Math.min(3, next.length)) + 1;

                for (let i = 0; i < numUpdates; i++) {
                    const idx = Math.floor(Math.random() * next.length);
                    const asset = next[idx];

                    if (asset.status === 'Online' && Math.random() < 0.01) {
                        asset.status = 'Offline';
                        setAlerts(prev => [`Alert: ${asset.feature_type} (${asset.feature_code}) went OFFLINE`, ...prev].slice(0, 5));
                    } else if (asset.status === 'Offline' && Math.random() < 0.1) {
                        asset.status = 'Online';
                    }
                    asset.lastPing = new Date().toISOString();
                }
                return next;
            });
        }, 2000);

        return () => clearInterval(interval);
    }, [initialAssets, seededAssets]);

    const stableAssetsWithStatus = assetsInSync ? assetsWithStatus : seededAssets;

    return { assetsWithStatus: stableAssetsWithStatus, alerts };
};

// Hook for real IoT sensor data
export const useSensorData = (assetId: string | null, refreshInterval: number = 60000) => {
    const [data, setData] = useState<AssetIoTData | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        if (!assetId) {
            setData(null);
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const iotData = await iotApi.getAssetIoTData(assetId, 24);
            setData(iotData);
        } catch (err: unknown) {
            setError(getErrorMessage(err, 'Failed to fetch IoT data'));
            setData(null);
        } finally {
            setLoading(false);
        }
    }, [assetId]);

    useEffect(() => {
        fetchData();

        if (refreshInterval > 0 && assetId) {
            const interval = setInterval(fetchData, refreshInterval);
            return () => clearInterval(interval);
        }
    }, [assetId, refreshInterval, fetchData]);

    return { data, loading, error, refetch: fetchData };
};

// Hook for IoT alerts
export const useIoTAlerts = (refreshInterval: number = 30000) => {
    const [alerts, setAlerts] = useState<IoTAlert[]>([]);
    const [loading, setLoading] = useState(false);

    const fetchAlerts = useCallback(async () => {
        setLoading(true);
        try {
            const data = await iotApi.getAlerts(false); // Only unacknowledged
            setAlerts(data);
        } catch (err) {
            console.error('Failed to fetch alerts:', err);
        } finally {
            setLoading(false);
        }
    }, []);

    const acknowledgeAlert = useCallback(async (alertId: string) => {
        try {
            await iotApi.acknowledgeAlert(alertId);
            setAlerts(prev => prev.filter(a => a._id !== alertId));
        } catch (err) {
            console.error('Failed to acknowledge alert:', err);
        }
    }, []);

    useEffect(() => {
        fetchAlerts();

        if (refreshInterval > 0) {
            const interval = setInterval(fetchAlerts, refreshInterval);
            return () => clearInterval(interval);
        }
    }, [refreshInterval, fetchAlerts]);

    return { alerts, loading, acknowledgeAlert, refetch: fetchAlerts };
};
