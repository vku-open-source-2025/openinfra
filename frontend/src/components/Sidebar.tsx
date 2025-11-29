import React from 'react';
import { Link } from 'react-router-dom';
import { LayoutDashboard, Map, Wrench, Settings, Activity } from 'lucide-react';

interface SidebarProps {
    activeTab: string;
    setActiveTab: (tab: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab }) => {
    const menuItems = [
        { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
        { id: 'map', label: 'Map View', icon: Map },
        { id: 'maintenance', label: 'Maintenance', icon: Wrench },
        { id: 'analytics', label: 'Analytics', icon: Activity },
        { id: 'settings', label: 'Settings', icon: Settings },
    ];

    return (
        <div className="h-screen w-64 bg-slate-900 text-white flex flex-col shadow-xl">
            <Link to="/" className="p-6 border-b border-slate-800 block hover:bg-slate-800/40 transition-colors">
                <div className="flex items-center gap-3">
                    <div className="bg-blue-500 p-2 rounded-lg">
                        <Activity size={24} />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold tracking-tight">InfraManager</h1>
                        <p className="text-xs text-slate-400">v1.0.0</p>
                    </div>
                </div>
            </Link>

            <nav className="flex-1 p-4 space-y-2">
                {menuItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = activeTab === item.id;
                    return (
                        <button
                            key={item.id}
                            onClick={() => setActiveTab(item.id)}
                            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${isActive
                                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/20'
                                    : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                                }`}
                        >
                            <Icon size={20} />
                            <span className="font-medium">{item.label}</span>
                            {isActive && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-white" />}
                        </button>
                    );
                })}
            </nav>

            <div className="p-4 border-t border-slate-800">
                <div className="bg-slate-800/50 rounded-lg p-4">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500 flex items-center justify-center font-bold text-xs">
                            AD
                        </div>
                        <div>
                            <p className="text-sm font-medium">Admin User</p>
                            <p className="text-xs text-slate-400">admin@system.com</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Sidebar;
