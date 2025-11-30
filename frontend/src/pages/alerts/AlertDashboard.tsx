import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { alertsApi } from "../../api/alerts";
import { AlertCard } from "../../components/alerts/AlertCard";
import { AlertActions } from "../../components/alerts/AlertActions";
import { Select } from "../../components/ui/select";
import {
    Tabs,
    TabsList,
    TabsTrigger,
    TabsContent,
} from "../../components/ui/tabs";
import { Skeleton } from "../../components/ui/skeleton";
import { AlertTriangle, Activity, CheckCircle } from "lucide-react";
import { useAuthStore } from "../../stores/authStore";

const AlertDashboard: React.FC = () => {
    const { user } = useAuthStore();
    const queryClient = useQueryClient();
    const [selectedSeverity, setSelectedSeverity] = useState<string>("");
    const [selectedStatus, setSelectedStatus] = useState<string>("active");

    const { data: alerts, isLoading } = useQuery({
        queryKey: ["alerts", "dashboard", selectedSeverity, selectedStatus],
        queryFn: () =>
            alertsApi.list({
                limit: 50,
                severity: selectedSeverity || undefined,
                status: selectedStatus || undefined,
            }),
        refetchInterval: 30000, // Refresh every 30 seconds
    });

    const acknowledgeMutation = useMutation({
        mutationFn: (id: string) => alertsApi.acknowledge(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["alerts"] });
        },
    });

    const resolveMutation = useMutation({
        mutationFn: ({ id, notes }: { id: string; notes?: string }) =>
            alertsApi.resolve(
                id,
                notes ? { resolution_notes: notes } : undefined
            ),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["alerts"] });
        },
    });

    const dismissMutation = useMutation({
        mutationFn: (id: string) => alertsApi.dismiss(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["alerts"] });
        },
    });

    const canManage =
        user?.role === "admin" ||
        user?.role === "manager" ||
        user?.role === "technician";

    const criticalAlerts =
        alerts?.filter(
            (a) => a.severity === "critical" && a.status === "active"
        ) || [];
    const highAlerts =
        alerts?.filter((a) => a.severity === "high" && a.status === "active") ||
        [];
    const activeAlerts = alerts?.filter((a) => a.status === "active") || [];
    const resolvedAlerts = alerts?.filter((a) => a.status === "resolved") || [];

    if (isLoading) {
        return (
            <div className="p-6 space-y-4">
                <Skeleton className="h-8 w-64" />
                <Skeleton className="h-64 w-full" />
            </div>
        );
    }

    return (
        <div className="p-6 space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900">
                        Alerts Dashboard
                    </h1>
                    <p className="text-slate-500 mt-1">
                        Monitor and manage system alerts
                    </p>
                </div>
                <div className="flex gap-2">
                    <Select
                        value={selectedSeverity}
                        onChange={(e) => setSelectedSeverity(e.target.value)}
                        placeholder="All Severities"
                    >
                        <option value="">All Severities</option>
                        <option value="critical">Critical</option>
                        <option value="high">High</option>
                        <option value="medium">Medium</option>
                        <option value="low">Low</option>
                    </Select>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white rounded-lg border border-slate-200 p-4">
                    <div className="flex items-center gap-2 mb-2">
                        <AlertTriangle className="h-5 w-5 text-red-500" />
                        <span className="text-sm font-medium text-slate-600">
                            Critical
                        </span>
                    </div>
                    <div className="text-2xl font-bold text-red-600">
                        {criticalAlerts.length}
                    </div>
                </div>
                <div className="bg-white rounded-lg border border-slate-200 p-4">
                    <div className="flex items-center gap-2 mb-2">
                        <Activity className="h-5 w-5 text-amber-500" />
                        <span className="text-sm font-medium text-slate-600">
                            High
                        </span>
                    </div>
                    <div className="text-2xl font-bold text-amber-600">
                        {highAlerts.length}
                    </div>
                </div>
                <div className="bg-white rounded-lg border border-slate-200 p-4">
                    <div className="flex items-center gap-2 mb-2">
                        <AlertTriangle className="h-5 w-5 text-blue-500" />
                        <span className="text-sm font-medium text-slate-600">
                            Active
                        </span>
                    </div>
                    <div className="text-2xl font-bold text-blue-600">
                        {activeAlerts.length}
                    </div>
                </div>
                <div className="bg-white rounded-lg border border-slate-200 p-4">
                    <div className="flex items-center gap-2 mb-2">
                        <CheckCircle className="h-5 w-5 text-green-500" />
                        <span className="text-sm font-medium text-slate-600">
                            Resolved
                        </span>
                    </div>
                    <div className="text-2xl font-bold text-green-600">
                        {resolvedAlerts.length}
                    </div>
                </div>
            </div>

            <Tabs defaultValue="active" onValueChange={setSelectedStatus}>
                <TabsList>
                    <TabsTrigger value="active">Active</TabsTrigger>
                    <TabsTrigger value="acknowledged">Acknowledged</TabsTrigger>
                    <TabsTrigger value="resolved">Resolved</TabsTrigger>
                    <TabsTrigger value="dismissed">Dismissed</TabsTrigger>
                </TabsList>

                <TabsContent value="active" className="mt-4">
                    <div className="space-y-4">
                        {alerts
                            ?.filter((a) => a.status === "active")
                            .map((alert) => (
                                <div
                                    key={alert.id}
                                    className="bg-white rounded-lg border border-slate-200 p-4"
                                >
                                    <AlertCard alert={alert} />
                                    {canManage && (
                                        <div className="mt-4 pt-4 border-t">
                                            <AlertActions
                                                alert={alert}
                                                onAcknowledge={async () => {
                                                    await acknowledgeMutation.mutateAsync(
                                                        alert.id
                                                    );
                                                }}
                                                onResolve={async (notes) => {
                                                    await resolveMutation.mutateAsync(
                                                        { id: alert.id, notes }
                                                    );
                                                }}
                                                onDismiss={async () => {
                                                    await dismissMutation.mutateAsync(
                                                        alert.id
                                                    );
                                                }}
                                                canAcknowledge={canManage}
                                                canResolve={canManage}
                                                canDismiss={canManage}
                                            />
                                        </div>
                                    )}
                                </div>
                            ))}
                        {alerts?.filter((a) => a.status === "active").length ===
                            0 && (
                            <div className="text-center py-12 text-slate-500">
                                <p>No active alerts</p>
                            </div>
                        )}
                    </div>
                </TabsContent>

                <TabsContent value="acknowledged" className="mt-4">
                    <div className="space-y-4">
                        {alerts
                            ?.filter((a) => a.status === "acknowledged")
                            .map((alert) => (
                                <AlertCard key={alert.id} alert={alert} />
                            ))}
                        {alerts?.filter((a) => a.status === "acknowledged")
                            .length === 0 && (
                            <div className="text-center py-12 text-slate-500">
                                <p>No acknowledged alerts</p>
                            </div>
                        )}
                    </div>
                </TabsContent>

                <TabsContent value="resolved" className="mt-4">
                    <div className="space-y-4">
                        {alerts
                            ?.filter((a) => a.status === "resolved")
                            .map((alert) => (
                                <AlertCard key={alert.id} alert={alert} />
                            ))}
                        {alerts?.filter((a) => a.status === "resolved")
                            .length === 0 && (
                            <div className="text-center py-12 text-slate-500">
                                <p>No resolved alerts</p>
                            </div>
                        )}
                    </div>
                </TabsContent>

                <TabsContent value="dismissed" className="mt-4">
                    <div className="space-y-4">
                        {alerts
                            ?.filter((a) => a.status === "dismissed")
                            .map((alert) => (
                                <AlertCard key={alert.id} alert={alert} />
                            ))}
                        {alerts?.filter((a) => a.status === "dismissed")
                            .length === 0 && (
                            <div className="text-center py-12 text-slate-500">
                                <p>No dismissed alerts</p>
                            </div>
                        )}
                    </div>
                </TabsContent>
            </Tabs>
        </div>
    );
};

export default AlertDashboard;
