import { Outlet } from "@tanstack/react-router";
import Sidebar from "../Sidebar";

export const AdminLayout: React.FC = () => {
    return (
        <div className="flex h-screen bg-slate-50 font-sans text-slate-900">
            <Sidebar />
            <main className="flex-1 flex flex-col overflow-hidden lg:ml-0">
                <Outlet />
            </main>
        </div>
    );
};
