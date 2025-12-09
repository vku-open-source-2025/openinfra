import { createFileRoute, Outlet, useNavigate } from "@tanstack/react-router";
import { useAuthStore } from "../stores/authStore";
import { useEffect } from "react";
import { Loader2 } from "lucide-react";
import Sidebar from "../components/Sidebar";
import { ProtectedRoute } from "../components/ProtectedRoute";

export const Route = createFileRoute("/technician")({
    component: TechnicianLayout,
});

function TechnicianLayout() {
    const { user, isAuthenticated } = useAuthStore();
    const navigate = useNavigate();

    useEffect(() => {
        if (!isAuthenticated) {
            navigate({ to: "/login" });
        } else if (
            user &&
            user.role !== "technician" &&
            user.role !== "admin" &&
            user.role !== "manager"
        ) {
            // Allow admin/manager to access technician routes for testing/support
            navigate({ to: "/" });
        }
    }, [user, isAuthenticated, navigate]);

    if (!user)
        return (
            <div className="h-screen flex items-center justify-center">
                <Loader2 className="animate-spin" />
            </div>
        );

    return (
        <ProtectedRoute>
            <div className="flex h-screen bg-slate-50 font-sans text-slate-900">
                <Sidebar />
                <main className="flex-1 flex flex-col overflow-y-auto lg:ml-0">
                    <Outlet />
                </main>
            </div>
        </ProtectedRoute>
    );
}
