import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
export const MainLayout = () => {
    return (_jsxs("div", { className: "flex h-screen bg-gray-100", children: [_jsx(Sidebar, {}), _jsxs("div", { className: "flex-1 flex flex-col overflow-hidden", children: [_jsx(Header, {}), _jsx("main", { className: "flex-1 overflow-x-hidden overflow-y-auto bg-gray-100", children: _jsx(Outlet, {}) })] })] }));
};
