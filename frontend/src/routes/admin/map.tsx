import { createFileRoute } from "@tanstack/react-router";
import AssetMapView from "../../pages/AssetMapView";

export const Route = createFileRoute("/admin/map")({
    component: AssetMapView,
    validateSearch: (search: Record<string, unknown>) => {
        return {
            assetId: search.assetId as string | undefined,
        };
    },
});
