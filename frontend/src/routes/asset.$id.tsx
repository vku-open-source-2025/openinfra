import { createFileRoute } from "@tanstack/react-router";
import AssetDetailPage from "../pages/AssetDetailPage";

export const Route = createFileRoute("/asset/$id")({
    component: AssetDetailPage,
});
