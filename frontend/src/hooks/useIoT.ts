import { useState, useEffect } from 'react';
import type { Asset } from '../api';

export const useIoT = (initialAssets: Asset[] | undefined) => {
    const [assetsWithStatus, setAssetsWithStatus] = useState<any[]>([]);
    const [alerts, setAlerts] = useState<string[]>([]);

    useEffect(() => {
        if (!initialAssets) return;

        // Initialize with random status
        const initialized = initialAssets.map(a => ({
            ...a,
            status: Math.random() > 0.05 ? 'Online' : 'Offline',
            lastPing: new Date().toISOString()
        }));
        setAssetsWithStatus(initialized);
    }, [initialAssets]);

    useEffect(() => {
        if (assetsWithStatus.length === 0) return;

        const interval = setInterval(() => {
            setAssetsWithStatus(current => {
                // Randomly flip status of 1-3 assets
                const next = [...current];
                const numUpdates = Math.floor(Math.random() * 3) + 1;

                for (let i = 0; i < numUpdates; i++) {
                    const idx = Math.floor(Math.random() * next.length);
                    const asset = next[idx];

                    // 1% chance to go offline if online, 10% chance to come back online
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
        }, 2000); // Update every 2 seconds

        return () => clearInterval(interval);
    }, [assetsWithStatus.length]);

    return { assetsWithStatus, alerts };
};
