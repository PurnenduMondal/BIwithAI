import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useRef, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { BellIcon, UserCircleIcon, Cog6ToothIcon, ArrowRightOnRectangleIcon, } from '@heroicons/react/24/outline';
export const Header = () => {
    const { user, logout } = useAuth();
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const menuRef = useRef(null);
    // Close menu when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (menuRef.current && !menuRef.current.contains(event.target)) {
                setIsMenuOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);
    return (_jsx("header", { className: "bg-white shadow-sm border-b border-gray-200", children: _jsxs("div", { className: "flex items-center justify-between px-6 py-4", children: [_jsx("div", { className: "flex items-center", children: _jsx("h1", { className: "text-xl font-semibold text-gray-800", children: "BI Dashboard Generator" }) }), _jsxs("div", { className: "flex items-center gap-4", children: [_jsxs("button", { className: "p-2 text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-100 relative", children: [_jsx(BellIcon, { className: "w-6 h-6" }), _jsx("span", { className: "absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" })] }), _jsxs("div", { className: "relative", ref: menuRef, children: [_jsxs("button", { onClick: () => setIsMenuOpen(!isMenuOpen), className: "flex items-center gap-2 p-2 rounded-lg hover:bg-gray-100", children: [_jsx(UserCircleIcon, { className: "w-8 h-8 text-gray-600" }), _jsxs("div", { className: "text-left", children: [_jsx("p", { className: "text-sm font-medium text-gray-900", children: user?.full_name || user?.email }), _jsx("p", { className: "text-xs text-gray-500 capitalize", children: user?.role })] })] }), isMenuOpen && (_jsx("div", { className: "absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg ring-1 ring-black ring-opacity-5 z-50", children: _jsxs("div", { className: "py-1", children: [_jsxs("a", { href: "/settings", className: "flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100", onClick: () => setIsMenuOpen(false), children: [_jsx(Cog6ToothIcon, { className: "w-5 h-5 mr-3" }), "Settings"] }), _jsxs("button", { onClick: () => {
                                                    setIsMenuOpen(false);
                                                    logout();
                                                }, className: "flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100", children: [_jsx(ArrowRightOnRectangleIcon, { className: "w-5 h-5 mr-3" }), "Logout"] })] }) }))] })] })] }) }));
};
