import { createFileRoute, Outlet, useNavigate } from '@tanstack/react-router';
import { useAuthStore } from '../stores/authStore';
import { useEffect } from 'react';
import { Loader2 } from 'lucide-react';

export const Route = createFileRoute('/technician')({
    component: TechnicianLayout,
});

function TechnicianLayout() {
    const { user, isAuthenticated } = useAuthStore();
    const navigate = useNavigate();

    useEffect(() => {
        if (!isAuthenticated) {
            navigate({ to: '/login' });
        } else if (user && user.role !== 'technician' && user.role !== 'admin') {
            // Optionally restrict if stricter role checks needed, but admin/tech is fine
            // navigate({ to: '/' }); 
        }
    }, [user, isAuthenticated, navigate]);

    if (!user) return <div className="h-screen flex items-center justify-center"><Loader2 className="animate-spin" /></div>;

    return (
        <div className="min-h-screen bg-slate-50 pb-16">
            <header className="bg-blue-600 text-white p-4 shadow-sm sticky top-0 z-10">
                <h1 className="font-bold text-lg">Field Technician</h1>
            </header>
            <main className="p-4">
                <Outlet />
            </main>
            {/* Mobile Bottom Nav could go here */}
        </div>
    );
}
