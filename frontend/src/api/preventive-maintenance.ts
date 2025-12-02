import { httpClient } from "../lib/httpClient";
import type {
    PreventiveMaintenancePlan,
    PreventiveMaintenancePlanCreateRequest,
    PreventiveMaintenancePlanUpdateRequest,
    PreventiveMaintenanceTask,
} from "../types/preventive-maintenance";
import {
    mockPreventiveMaintenancePlan,
    mockUpcomingTasks,
    mockOverdueTasks,
    delay,
} from "./mocks/assetLifecycleMocks";

// Set to true to use mock data instead of real API calls
const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === "true" || false;

export const preventiveMaintenanceApi = {
    getPlan: async (
        assetId: string
    ): Promise<PreventiveMaintenancePlan | null> => {
        if (USE_MOCK_DATA) {
            await delay(300);
            return mockPreventiveMaintenancePlan(assetId);
        }
        const response = await httpClient.get<PreventiveMaintenancePlan | null>(
            `/assets/${assetId}/preventive-maintenance`
        );
        return response.data;
    },

    createPlan: async (
        data: PreventiveMaintenancePlanCreateRequest
    ): Promise<PreventiveMaintenancePlan> => {
        const response = await httpClient.post<PreventiveMaintenancePlan>(
            "/preventive-maintenance",
            data
        );
        return response.data;
    },

    updatePlan: async (
        planId: string,
        data: PreventiveMaintenancePlanUpdateRequest
    ): Promise<PreventiveMaintenancePlan> => {
        const response = await httpClient.put<PreventiveMaintenancePlan>(
            `/preventive-maintenance/${planId}`,
            data
        );
        return response.data;
    },

    getUpcomingTasks: async (
        assetId: string
    ): Promise<PreventiveMaintenanceTask[]> => {
        if (USE_MOCK_DATA) {
            await delay(300);
            return mockUpcomingTasks(assetId);
        }
        const response = await httpClient.get<PreventiveMaintenanceTask[]>(
            `/assets/${assetId}/preventive-maintenance/tasks`
        );
        return response.data;
    },

    getOverdueTasks: async (
        assetId: string
    ): Promise<PreventiveMaintenanceTask[]> => {
        if (USE_MOCK_DATA) {
            await delay(300);
            return mockOverdueTasks(assetId);
        }
        const response = await httpClient.get<PreventiveMaintenanceTask[]>(
            `/assets/${assetId}/preventive-maintenance/overdue`
        );
        return response.data;
    },
};
