import { httpClient } from "../lib/httpClient";
import type {
    Maintenance,
    MaintenanceCreateRequest,
    MaintenanceUpdateRequest,
    MaintenanceStartRequest,
    MaintenanceCompleteRequest,
    MaintenanceApprovalRequest,
    MaintenanceFilterParams,
} from "../types/maintenance";
import { mockMaintenanceHistory, delay } from "./mocks/assetLifecycleMocks";

/**
 * Maintenance API Client
 *
 * Provides methods for managing maintenance work orders.
 * Supports technician workflows:
 * - List assigned maintenance work orders
 * - Start maintenance (scheduled -> in_progress)
 * - Complete maintenance (in_progress -> completed)
 * - Upload photos (before/after)
 * - Cancel maintenance
 *
 * API Base Path: /api/v1/maintenance
 *
 * @see API_DOCUMENTATION.md for detailed endpoint specifications
 */

// Set to true to use mock data instead of real API calls
const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === "true" || false;

export interface MaintenanceListParams {
    skip?: number;
    limit?: number;
    asset_id?: string;
    status?: string;
    assigned_to?: string;
    priority?: string;
}

/**
 * Maintenance API - Handles all maintenance work order operations
 * Supports technician workflows: list, start, complete, upload photos, cancel
 */
export const maintenanceApi = {
    /**
     * List maintenance work orders
     * @param params - Filter parameters: skip, limit, asset_id, status, assigned_to, priority
     */
    list: async (params?: MaintenanceListParams): Promise<Maintenance[]> => {
        const response = await httpClient.get<Maintenance[]>("/maintenance", {
            params,
        });
        return response.data;
    },

    /**
     * Get upcoming maintenance work orders
     * @param days - Number of days to look ahead (default: 7, max: 30)
     */
    getUpcoming: async (days?: number): Promise<Maintenance[]> => {
        const response = await httpClient.get<Maintenance[]>(
            "/maintenance/upcoming",
            {
                params: days ? { days } : undefined,
            }
        );
        return response.data;
    },

    /**
     * Get maintenance work order by ID
     * @param id - Maintenance work order ID
     */
    getById: async (id: string): Promise<Maintenance> => {
        const response = await httpClient.get<Maintenance>(
            `/maintenance/${id}`
        );
        return response.data;
    },

    create: async (data: MaintenanceCreateRequest): Promise<Maintenance> => {
        const response = await httpClient.post<Maintenance>(
            "/maintenance",
            data
        );
        return response.data;
    },

    update: async (
        id: string,
        data: MaintenanceUpdateRequest
    ): Promise<Maintenance> => {
        const response = await httpClient.put<Maintenance>(
            `/maintenance/${id}`,
            data
        );
        return response.data;
    },

    assign: async (id: string, assignedTo: string): Promise<Maintenance> => {
        const response = await httpClient.post<Maintenance>(
            `/maintenance/${id}/assign`,
            null,
            {
                params: { assigned_to: assignedTo },
            }
        );
        return response.data;
    },

    /**
     * Start maintenance work order
     * Changes status from 'scheduled' to 'in_progress'
     * @param id - Maintenance work order ID
     * @param data - Optional start time (ISO datetime string). If not provided, backend uses current time.
     */
    start: async (
        id: string,
        data?: MaintenanceStartRequest
    ): Promise<Maintenance> => {
        const response = await httpClient.post<Maintenance>(
            `/maintenance/${id}/start`,
            data || {}
        );
        return response.data;
    },

    /**
     * Complete maintenance work order
     * Changes status from 'in_progress' to 'completed'
     * @param id - Maintenance work order ID
     * @param data - Completion details: work_performed (required), actual_cost (optional), quality_checks (optional array)
     */
    complete: async (
        id: string,
        data: MaintenanceCompleteRequest
    ): Promise<Maintenance> => {
        if (!data.work_performed || !data.work_performed.trim()) {
            throw new Error("Mô tả công việc thực hiện là bắt buộc");
        }
        const response = await httpClient.post<Maintenance>(
            `/maintenance/${id}/complete`,
            {
                work_performed: data.work_performed,
                completion_notes: data.completion_notes,
                actual_cost: data.actual_cost,
                quality_checks: data.quality_checks || [],
            }
        );
        return response.data;
    },

    /**
     * Cancel maintenance work order
     * Changes status to 'cancelled'
     * @param id - Maintenance work order ID
     * @param cancellationReason - Reason for cancellation (required)
     */
    cancel: async (
        id: string,
        cancellationReason: string
    ): Promise<Maintenance> => {
        if (!cancellationReason || !cancellationReason.trim()) {
            throw new Error("Cancellation reason is required");
        }
        const response = await httpClient.post<Maintenance>(
            `/maintenance/${id}/cancel`,
            null,
            {
                params: { cancellation_reason: cancellationReason },
            }
        );
        return response.data;
    },

    /**
     * Upload maintenance photos (before or after work)
     * @param id - Maintenance work order ID
     * @param files - Array of image files to upload
     * @param photoType - "before" or "after" (default: "after")
     */
    uploadPhotos: async (
        id: string,
        files: File[],
        photoType: "before" | "after" = "after"
    ): Promise<Maintenance> => {
        if (!files || files.length === 0) {
            throw new Error("At least one file is required");
        }
        const formData = new FormData();
        files.forEach((file) => {
            formData.append("files", file);
        });
        const response = await httpClient.post<Maintenance>(
            `/maintenance/${id}/photos`,
            formData,
            {
                params: { photo_type: photoType },
                headers: {
                    "Content-Type": "multipart/form-data",
                },
            }
        );
        return response.data;
    },

    /**
     * Get maintenance work orders for a specific asset
     * @param assetId - Asset ID
     * @param params - Pagination parameters: skip, limit
     */
    getByAsset: async (
        assetId: string,
        params?: { skip?: number; limit?: number }
    ): Promise<Maintenance[]> => {
        const response = await httpClient.get<Maintenance[]>(
            `/maintenance/asset/${assetId}`,
            { params }
        );
        return response.data;
    },

    getHistory: async (
        assetId: string,
        filters?: MaintenanceFilterParams
    ): Promise<Maintenance[]> => {
        if (USE_MOCK_DATA) {
            await delay(400);
            let history = mockMaintenanceHistory(assetId);

            // Apply filters
            if (filters) {
                if (filters.date_from) {
                    history = history.filter(
                        (m) =>
                            new Date(m.scheduled_date) >=
                            new Date(filters.date_from!)
                    );
                }
                if (filters.date_to) {
                    history = history.filter(
                        (m) =>
                            new Date(m.scheduled_date) <=
                            new Date(filters.date_to!)
                    );
                }
                if (filters.technician) {
                    history = history.filter((m) =>
                        m.technician
                            ?.toLowerCase()
                            .includes(filters.technician!.toLowerCase())
                    );
                }
                if (filters.cost_min !== undefined) {
                    history = history.filter(
                        (m) =>
                            (m.actual_cost || m.estimated_cost || 0) >=
                            filters.cost_min!
                    );
                }
                if (filters.cost_max !== undefined) {
                    history = history.filter(
                        (m) =>
                            (m.actual_cost || m.estimated_cost || 0) <=
                            filters.cost_max!
                    );
                }
                if (filters.approval_status) {
                    history = history.filter(
                        (m) => m.approval_status === filters.approval_status
                    );
                }
            }

            return history;
        }
        const response = await httpClient.get<Maintenance[]>(
            `/maintenance/asset/${assetId}`,
            { params: filters }
        );
        return response.data;
    },

    approve: async (
        id: string,
        data: MaintenanceApprovalRequest
    ): Promise<Maintenance> => {
        const response = await httpClient.post<Maintenance>(
            `/maintenance/${id}/approve`,
            data
        );
        return response.data;
    },

    reject: async (id: string, reason: string): Promise<Maintenance> => {
        const response = await httpClient.post<Maintenance>(
            `/maintenance/${id}/reject`,
            { rejection_reason: reason }
        );
        return response.data;
    },
};
