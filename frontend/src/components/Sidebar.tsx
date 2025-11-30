import React from "react";
import { Link, useLocation } from "@tanstack/react-router";
import {
    LayoutDashboard,
    Map,
    Settings,
    Activity,
    AlertTriangle,
    FileText,
    DollarSign,
    Radio,
    Users,
    ChevronRight,
    Menu,
    X,
} from "lucide-react";
import { useAuthStore } from "../stores/authStore";

interface SidebarProps {
    activeTab?: string;
    setActiveTab?: (tab: string) => void;
}

interface MenuItem {
    id: string;
    label: string;
    icon: React.ComponentType<{ size?: number; className?: string }>;
    path: string;
    badge?: number;
    children?: MenuItem[];
}

const Sidebar: React.FC<SidebarProps> = () => {
    const location = useLocation();
    const { user } = useAuthStore();
    const [expandedItems, setExpandedItems] = React.useState<Set<string>>(
        new Set()
    );
    const [isMobileOpen, setIsMobileOpen] = React.useState(false);

    const menuItems: MenuItem[] = [
        {
            id: "dashboard",
            label: "Dashboard",
            icon: LayoutDashboard,
            path: "/admin",
        },
        {
            id: "map",
            label: "Map View",
            icon: Map,
            path: "/map",
        },
        {
            id: "incidents",
            label: "Incidents",
            icon: AlertTriangle,
            path: "/admin/incidents",
            badge: 0, // Could be dynamic from state
        },
        {
            id: "alerts",
            label: "Alerts",
            icon: Activity,
            path: "/admin/alerts",
            badge: 0, // Could be dynamic from state
        },
        // Note: Maintenance and Assets routes can be added when pages are created
        // {
        //     id: 'maintenance',
        //     label: 'Maintenance',
        //     icon: Wrench,
        //     path: '/admin/maintenance',
        // },
        // {
        //     id: 'assets',
        //     label: 'Assets',
        //     icon: Map,
        //     path: '/admin/assets',
        // },
        {
            id: "iot",
            label: "IoT Sensors",
            icon: Radio,
            path: "/admin/iot",
        },
        {
            id: "budgets",
            label: "Budgets",
            icon: DollarSign,
            path: "/admin/budgets",
        },
        {
            id: "reports",
            label: "Reports",
            icon: FileText,
            path: "/admin/reports",
        },
        // Note: Analytics route can be added when page is created
        // {
        //     id: 'analytics',
        //     label: 'Analytics',
        //     icon: BarChart3,
        //     path: '/admin/analytics',
        // },
    ];

    // Admin-only items
    const adminItems: MenuItem[] = [
        {
            id: "users",
            label: "User Management",
            icon: Users,
            path: "/admin/users",
        },
    ];

    const allItems =
        user?.role === "admin" ? [...menuItems, ...adminItems] : menuItems;

    const toggleExpanded = (id: string) => {
        setExpandedItems((prev) => {
            const newSet = new Set(prev);
            if (newSet.has(id)) {
                newSet.delete(id);
            } else {
                newSet.add(id);
            }
            return newSet;
        });
    };

    const isActive = (path: string) => {
        return (
            location.pathname === path ||
            location.pathname.startsWith(path + "/")
        );
    };

    const isExpanded = (id: string) => expandedItems.has(id);

    return (
        <>
            {/* Mobile menu button */}
            <button
                onClick={() => setIsMobileOpen(!isMobileOpen)}
                className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-slate-900 text-white rounded-lg shadow-lg"
            >
                {isMobileOpen ? <X size={24} /> : <Menu size={24} />}
            </button>

            {/* Sidebar */}
            <div
                className={`fixed lg:static inset-y-0 left-0 z-40 w-64 bg-slate-900 text-white flex flex-col shadow-xl transform transition-transform duration-300 ease-in-out ${
                    isMobileOpen
                        ? "translate-x-0"
                        : "-translate-x-full lg:translate-x-0"
                }`}
            >
                {/* Logo Section */}
                <div className="p-6 border-b border-slate-800">
                    <Link
                        to="/admin"
                        className="flex items-center gap-3 hover:opacity-80 transition-opacity"
                    >
                        <div className="bg-blue-500 p-2 rounded-lg">
                            <Activity size={24} />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold tracking-tight">
                                InfraManager
                            </h1>
                            <p className="text-xs text-slate-400">v1.0.0</p>
                        </div>
                    </Link>
                </div>

                {/* Navigation */}
                <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
                    {allItems.map((item) => {
                        const Icon = item.icon;
                        const active = isActive(item.path);
                        const hasChildren =
                            item.children && item.children.length > 0;
                        const expanded = isExpanded(item.id);

                        if (hasChildren) {
                            return (
                                <div key={item.id}>
                                    <button
                                        onClick={() => toggleExpanded(item.id)}
                                        className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                                            active
                                                ? "bg-blue-600 text-white shadow-lg shadow-blue-900/20"
                                                : "text-slate-400 hover:bg-slate-800 hover:text-white"
                                        }`}
                                    >
                                        <Icon size={20} />
                                        <span className="font-medium flex-1 text-left">
                                            {item.label}
                                        </span>
                                        {item.badge !== undefined &&
                                            item.badge > 0 && (
                                                <span className="bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">
                                                    {item.badge}
                                                </span>
                                            )}
                                        <ChevronRight
                                            size={16}
                                            className={`transition-transform ${
                                                expanded ? "rotate-90" : ""
                                            }`}
                                        />
                                    </button>
                                    {expanded && item.children && (
                                        <div className="ml-4 mt-1 space-y-1">
                                            {item.children.map((child) => {
                                                const ChildIcon = child.icon;
                                                const childActive = isActive(
                                                    child.path
                                                );
                                                return (
                                                    <Link
                                                        key={child.id}
                                                        to={child.path}
                                                        className={`flex items-center gap-3 px-4 py-2 rounded-lg transition-all duration-200 ${
                                                            childActive
                                                                ? "bg-blue-600/50 text-white"
                                                                : "text-slate-400 hover:bg-slate-800 hover:text-white"
                                                        }`}
                                                    >
                                                        <ChildIcon size={16} />
                                                        <span className="text-sm">
                                                            {child.label}
                                                        </span>
                                                    </Link>
                                                );
                                            })}
                                        </div>
                                    )}
                                </div>
                            );
                        }

                        return (
                            <Link
                                key={item.id}
                                to={item.path}
                                onClick={() => setIsMobileOpen(false)}
                                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                                    active
                                        ? "bg-blue-600 text-white shadow-lg shadow-blue-900/20"
                                        : "text-slate-400 hover:bg-slate-800 hover:text-white"
                                }`}
                            >
                                <Icon size={20} />
                                <span className="font-medium flex-1">
                                    {item.label}
                                </span>
                                {item.badge !== undefined && item.badge > 0 && (
                                    <span className="bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">
                                        {item.badge}
                                    </span>
                                )}
                                {active && (
                                    <div className="ml-auto w-1.5 h-1.5 rounded-full bg-white" />
                                )}
                            </Link>
                        );
                    })}
                </nav>

                {/* User Section */}
                <div className="p-4 border-t border-slate-800">
                    <div className="bg-slate-800/50 rounded-lg p-4">
                        <div className="flex items-center gap-3 mb-2">
                            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500 flex items-center justify-center font-bold text-xs">
                                {user?.email?.charAt(0).toUpperCase() || "A"}
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium truncate">
                                    {user?.email || "Admin User"}
                                </p>
                                <p className="text-xs text-slate-400 capitalize">
                                    {user?.role || "admin"}
                                </p>
                            </div>
                        </div>
                        <Link
                            to="/admin/settings"
                            onClick={() => setIsMobileOpen(false)}
                            className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors"
                        >
                            <Settings size={16} />
                            <span>Settings</span>
                        </Link>
                    </div>
                </div>
            </div>

            {/* Mobile overlay */}
            {isMobileOpen && (
                <div
                    className="fixed inset-0 bg-black/50 z-30 lg:hidden"
                    onClick={() => setIsMobileOpen(false)}
                />
            )}
        </>
    );
};

export default Sidebar;
