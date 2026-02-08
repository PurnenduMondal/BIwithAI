import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useState } from 'react';
import {} from '@/types';
import { Button } from '@/components/common/Button';
import { Modal } from '@/components/common/Modal';
import { useDeleteDashboard, useDuplicateDashboard } from '@/hooks/useDashboard';
import { dashboardApi } from '@/api/dashboards';
import toast from 'react-hot-toast';
import { PencilIcon, TrashIcon, DocumentDuplicateIcon, ShareIcon, ArrowDownTrayIcon, } from '@heroicons/react/24/outline';
export const DashboardHeader = ({ dashboard, onEdit, isEditing }) => {
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [showShareModal, setShowShareModal] = useState(false);
    const [shareUrl, setShareUrl] = useState('');
    const deleteDashboard = useDeleteDashboard();
    const duplicateDashboard = useDuplicateDashboard();
    const handleShare = async () => {
        try {
            const { share_url } = await dashboardApi.share(dashboard.id);
            setShareUrl(share_url);
            setShowShareModal(true);
        }
        catch (error) {
            toast.error('Failed to generate share link');
        }
    };
    const handleDelete = () => {
        deleteDashboard.mutate(dashboard.id);
        setShowDeleteModal(false);
    };
    const handleDuplicate = () => {
        duplicateDashboard.mutate(dashboard.id);
    };
    return (_jsxs(_Fragment, { children: [_jsx("div", { className: "bg-white shadow-sm border-b border-gray-200 px-6 py-4", children: _jsxs("div", { className: "flex items-center justify-between", children: [_jsxs("div", { children: [_jsx("h1", { className: "text-2xl font-bold text-gray-900", children: dashboard.name }), dashboard.description && (_jsx("p", { className: "text-sm text-gray-600 mt-1", children: dashboard.description }))] }), _jsxs("div", { className: "flex items-center gap-2", children: [_jsxs(Button, { variant: "outline", size: "sm", onClick: onEdit, children: [_jsx(PencilIcon, { className: "w-4 h-4 mr-2" }), isEditing ? 'Done Editing' : 'Edit'] }), _jsxs(Button, { variant: "outline", size: "sm", onClick: handleDuplicate, children: [_jsx(DocumentDuplicateIcon, { className: "w-4 h-4 mr-2" }), "Duplicate"] }), _jsxs(Button, { variant: "outline", size: "sm", onClick: handleShare, children: [_jsx(ShareIcon, { className: "w-4 h-4 mr-2" }), "Share"] }), _jsxs(Button, { variant: "outline", size: "sm", children: [_jsx(ArrowDownTrayIcon, { className: "w-4 h-4 mr-2" }), "Export"] }), _jsxs(Button, { variant: "danger", size: "sm", onClick: () => setShowDeleteModal(true), children: [_jsx(TrashIcon, { className: "w-4 h-4 mr-2" }), "Delete"] })] })] }) }), _jsx(Modal, { isOpen: showDeleteModal, onClose: () => setShowDeleteModal(false), title: "Delete Dashboard", footer: _jsxs(_Fragment, { children: [_jsx(Button, { variant: "outline", onClick: () => setShowDeleteModal(false), children: "Cancel" }), _jsx(Button, { variant: "danger", onClick: handleDelete, children: "Delete" })] }), children: _jsxs("p", { className: "text-gray-600", children: ["Are you sure you want to delete \"", dashboard.name, "\"? This action cannot be undone."] }) }), _jsx(Modal, { isOpen: showShareModal, onClose: () => setShowShareModal(false), title: "Share Dashboard", footer: _jsx(Button, { onClick: () => setShowShareModal(false), children: "Close" }), children: _jsxs("div", { className: "space-y-4", children: [_jsx("p", { className: "text-gray-600", children: "Anyone with this link can view this dashboard:" }), _jsxs("div", { className: "flex items-center gap-2", children: [_jsx("input", { type: "text", value: shareUrl, readOnly: true, className: "flex-1 px-3 py-2 border rounded-lg bg-gray-50" }), _jsx(Button, { onClick: () => {
                                        navigator.clipboard.writeText(shareUrl);
                                        toast.success('Link copied to clipboard!');
                                    }, children: "Copy" })] })] }) })] }));
};
