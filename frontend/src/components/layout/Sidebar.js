import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { NavLink } from 'react-router-dom';
import { HomeIcon, ChartBarIcon, CircleStackIcon, BellAlertIcon, Cog6ToothIcon, } from '@heroicons/react/24/outline';
const navigation = [
    { name: 'Home', href: '/', icon: HomeIcon },
    { name: 'Dashboards', href: '/dashboards', icon: ChartBarIcon },
    { name: 'Data Sources', href: '/data-sources', icon: CircleStackIcon },
    { name: 'Alerts', href: '/alerts', icon: BellAlertIcon },
    { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
];
export const Sidebar = () => {
    return (_jsxs("aside", { className: "w-64 bg-gray-900 text-white", children: [_jsx("div", { className: "flex items-center justify-center h-16 border-b border-gray-800", children: _jsx("h1", { className: "text-xl font-bold", children: "BI Dashboard" }) }), _jsx("nav", { className: "mt-8", children: _jsx("div", { className: "px-4 space-y-2", children: navigation.map((item) => (_jsxs(NavLink, { to: item.href, className: ({ isActive }) => `flex items-center px-4 py-3 text-sm font-medium rounded-lg transition ${isActive
                            ? 'bg-gray-800 text-white'
                            : 'text-gray-300 hover:bg-gray-800 hover:text-white'}`, children: [_jsx(item.icon, { className: "w-5 h-5 mr-3" }), item.name] }, item.name))) }) })] }));
};
