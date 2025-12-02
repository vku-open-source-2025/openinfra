import { createFileRoute } from "@tanstack/react-router";
import { AdminLayout } from "../components/Layout/AdminLayout";
import { ProtectedRoute } from "../components/ProtectedRoute";

export const Route = createFileRoute("/admin")({
    component: () => (
        <ProtectedRoute>
            <AdminLayout />
        </ProtectedRoute>
    ),
});
