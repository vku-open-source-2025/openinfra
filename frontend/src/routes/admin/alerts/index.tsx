import { createFileRoute } from "@tanstack/react-router";
import AlertDashboard from "@/pages/alerts/AlertDashboard";

export const Route = createFileRoute("/admin/alerts/")({
    component: AlertDashboard,
});
