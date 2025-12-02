import { createFileRoute } from "@tanstack/react-router";
import AssetList from "@/pages/admin/AssetList";

export const Route = createFileRoute("/admin/assets/")({
    component: AssetList,
});
