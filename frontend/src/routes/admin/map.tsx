import { createFileRoute } from "@tanstack/react-router";
import AdminMap from "@/pages/admin/AdminMap";

export const Route = createFileRoute("/admin/map")({
    component: AdminMap,
    validateSearch: (search: Record<string, unknown>) => {
        return {
            assetId: search.assetId as string | undefined,
        };
    },
});
