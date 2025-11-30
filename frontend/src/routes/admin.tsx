import { createFileRoute, Outlet } from "@tanstack/react-router";
import { ProtectedRoute } from "../components/ProtectedRoute";
import { AdminLayout } from "../components/Layout/AdminLayout";

export const Route = createFileRoute("/admin")({
    component: () => (
        <ProtectedRoute>
            <AdminLayout />
        </ProtectedRoute>
    ),
});
