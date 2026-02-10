import { useState, useEffect } from 'react';
import { type DashboardHeaderProps } from '../../types';
import { Button } from '../common/Button';
import { Modal } from '../common/Modal';
import { useDeleteDashboard, useDuplicateDashboard, useUpdateDashboard } from '../../hooks/useDashboard';
import { dashboardApi } from '../../api/dashboards';
import { exportApi, type ExportFormat } from '../../api/exports';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useNotifications } from '../../contexts/NotificationContext';
import { useExports } from '../../contexts/ExportContext';
import { exportDashboardScreenshot, downloadBlob } from '../../utils/exportUtils';
import toast from 'react-hot-toast';
import {
  PencilIcon,
  TrashIcon,
  DocumentDuplicateIcon,
  ShareIcon,
  ArrowDownTrayIcon,
  PlusIcon,
  CheckIcon,
} from '@heroicons/react/24/outline';

export const DashboardHeader = ({ dashboard, onEdit, isEditing, onAddWidget, onSave }: DashboardHeaderProps) => {
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [shareUrl, setShareUrl] = useState('');
  const [editedName, setEditedName] = useState(dashboard.name);
  const [editedDescription, setEditedDescription] = useState(dashboard.description || '');
  const [selectedExportFormat, setSelectedExportFormat] = useState<ExportFormat>('pdf');
  const [isSharing, setIsSharing] = useState(false);
  const [currentExportJobId, setCurrentExportJobId] = useState<string | null>(null);
  
  const deleteDashboard = useDeleteDashboard();
  const duplicateDashboard = useDuplicateDashboard();
  const updateDashboard = useUpdateDashboard(dashboard.id);
  const { lastMessage, subscribe, unsubscribe } = useWebSocket();
  const { addNotification } = useNotifications();
  const { addExport, updateExport } = useExports();

  // Listen for export updates via websocket
  useEffect(() => {
    if (!lastMessage || !currentExportJobId) return;

    console.log('Received websocket message:', lastMessage);

    if (lastMessage.type === 'export_progress') {
      const { job_id, progress, message } = lastMessage;
      
      console.log('Export progress:', { job_id, progress, message, currentExportJobId });
      
      if (job_id === currentExportJobId) {
        updateExport(job_id, {
          progress: progress || 0,
          message: message || '',
          status: 'processing',
        });
      }
    } else if (lastMessage.type === 'export_completed') {
      const { job_id, download_url, format } = lastMessage;
      
      if (job_id === currentExportJobId) {
        updateExport(job_id, {
          status: 'completed',
          progress: 100,
          downloadUrl: download_url,
          message: 'Export completed',
        });
        
        addNotification({
          type: 'export',
          title: 'Export Complete',
          message: `Dashboard exported as ${format.toUpperCase()}`,
          downloadUrl: download_url,
        });
        
        toast.success('Export completed! Check export queue.');
        setCurrentExportJobId(null);
      }
    } else if (lastMessage.type === 'export_failed') {
      const { job_id, error } = lastMessage;
      
      if (job_id === currentExportJobId) {
        updateExport(job_id, {
          status: 'failed',
          error: error || 'Export failed',
          message: 'Export failed',
        });
        
        toast.error(error || 'Export failed');
        setCurrentExportJobId(null);
      }
    }
  }, [lastMessage, currentExportJobId, addNotification, updateExport]);

  const handleShare = async () => {
    setIsSharing(true);
    try {
      const { share_url } = await dashboardApi.share(dashboard.id);
      setShareUrl(share_url);
      setShowShareModal(true);
      toast.success('Share link generated!');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to generate share link');
    } finally {
      setIsSharing(false);
    }
  };

  const handleExport = async () => {
    setShowExportModal(false);
    
    try {
      toast.loading('Generating export...', { id: 'export-loading' });
      
      // Use frontend screenshot-based export
      const blob = await exportDashboardScreenshot({
        filename: `${dashboard.name}.${selectedExportFormat}`,
        format: selectedExportFormat === 'pdf' ? 'pdf' : 'png',
      });
      
      // Download the file
      downloadBlob(
        blob,
        `${dashboard.name}.${selectedExportFormat === 'pdf' ? 'pdf' : 'png'}`
      );
      
      toast.success('Dashboard exported successfully!', { id: 'export-loading' });
    } catch (error: any) {
      console.error('Export error:', error);
      toast.error(error.message || 'Failed to export dashboard', { id: 'export-loading' });
    }
  };

  // Cleanup websocket subscription
  useEffect(() => {
    return () => {
      if (currentExportJobId) {
        unsubscribe('export_job', currentExportJobId);
      }
    };
  }, [currentExportJobId, unsubscribe]);

  const handleDelete = () => {
    deleteDashboard.mutate(dashboard.id);
    setShowDeleteModal(false);
  };

  const handleDuplicate = () => {
    duplicateDashboard.mutate(dashboard.id);
  };

  const handleEditDashboard = () => {
    setEditedName(dashboard.name);
    setEditedDescription(dashboard.description || '');
    setShowEditModal(true);
  };

  const handleSaveEdit = () => {
    updateDashboard.mutate({
      name: editedName,
      description: editedDescription,
    });
    setShowEditModal(false);
  };

  const handleSave = () => {
    if (onSave) {
      onSave();
    }
  };

  return (
    <>
      <div className="bg-white shadow-sm border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{dashboard.name}</h1>
            {dashboard.description && (
              <p className="text-sm text-gray-600 mt-1">{dashboard.description}</p>
            )}
          </div>

          <div className="flex items-center gap-2" data-export-exclude>
            {isEditing && onAddWidget && (
              <Button
                variant="primary"
                size="sm"
                onClick={onAddWidget}
              >
                <PlusIcon className="w-4 h-4 mr-2" />
                Add Widget
              </Button>
            )}

            {isEditing && onSave && (
              <Button
                variant="primary"
                size="sm"
                onClick={handleSave}
              >
                <CheckIcon className="w-4 h-4 mr-2" />
                Save Changes
              </Button>
            )}
            
            {!isEditing && (
              <Button
                variant="outline"
                size="sm"
                onClick={onEdit}
              >
                <PencilIcon className="w-4 h-4 mr-2" />
                Edit Layout
              </Button>
            )}

            <Button
              variant="outline"
              size="sm"
              onClick={handleEditDashboard}
            >
              <PencilIcon className="w-4 h-4 mr-2" />
              Edit Details
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={handleDuplicate}
            >
              <DocumentDuplicateIcon className="w-4 h-4 mr-2" />
              Duplicate
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={handleShare}
              isLoading={isSharing}
            >
              <ShareIcon className="w-4 h-4 mr-2" />
              Share
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowExportModal(true)}
            >
              <ArrowDownTrayIcon className="w-4 h-4 mr-2" />
              Export
            </Button>

            <Button
              variant="danger"
              size="sm"
              onClick={() => setShowDeleteModal(true)}
            >
              <TrashIcon className="w-4 h-4 mr-2" />
              Delete
            </Button>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        title="Delete Dashboard"
        footer={
          <>
            <Button variant="outline" onClick={() => setShowDeleteModal(false)}>
              Cancel
            </Button>
            <Button variant="danger" onClick={handleDelete}>
              Delete
            </Button>
          </>
        }
      >
        <p className="text-gray-600">
          Are you sure you want to delete "{dashboard.name}"? This action cannot be undone.
        </p>
      </Modal>

      {/* Share Modal */}
      <Modal
        isOpen={showShareModal}
        onClose={() => setShowShareModal(false)}
        title="Share Dashboard"
        footer={
          <Button onClick={() => setShowShareModal(false)}>
            Close
          </Button>
        }
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            Anyone with this link can view this dashboard:
          </p>
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={shareUrl}
              readOnly
              className="flex-1 px-3 py-2 border rounded-lg bg-gray-50"
            />
            <Button
              onClick={() => {
                navigator.clipboard.writeText(shareUrl);
                toast.success('Link copied to clipboard!');
              }}
            >
              Copy
            </Button>
          </div>
        </div>
      </Modal>

      {/* Edit Dashboard Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="Edit Dashboard Details"
        footer={
          <>
            <Button variant="outline" onClick={() => setShowEditModal(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSaveEdit}
              disabled={!editedName.trim()}
              isLoading={updateDashboard.isPending}
            >
              Save
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Dashboard Name
            </label>
            <input
              type="text"
              value={editedName}
              onChange={(e) => setEditedName(e.target.value)}
              placeholder="Enter dashboard name"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description (optional)
            </label>
            <textarea
              value={editedDescription}
              onChange={(e) => setEditedDescription(e.target.value)}
              placeholder="Enter dashboard description"
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
          </div>
        </div>
      </Modal>

      {/* Export Modal */}
      <Modal
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
        title="Export Dashboard"
        footer={
          <>
            <Button 
              variant="outline" 
              onClick={() => setShowExportModal(false)}
            >
              Cancel
            </Button>
            <Button onClick={handleExport}>
              Start Export
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            Choose a format to export your dashboard:
          </p>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Export Format
            </label>
            <div className="space-y-2">
              <label className="flex items-center p-3 border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50">
                <input
                  type="radio"
                  name="exportFormat"
                  value="pdf"
                  checked={selectedExportFormat === 'pdf'}
                  onChange={(e) => setSelectedExportFormat(e.target.value as ExportFormat)}
                  className="mr-3"
                />
                <div>
                  <div className="font-medium text-gray-900">PDF</div>
                  <div className="text-sm text-gray-600">Portable document with all widgets and data</div>
                </div>
              </label>
              <label className="flex items-center p-3 border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50">
                <input
                  type="radio"
                  name="exportFormat"
                  value="png"
                  checked={selectedExportFormat === 'png'}
                  onChange={(e) => setSelectedExportFormat(e.target.value as ExportFormat)}
                  className="mr-3"
                />
                <div>
                  <div className="font-medium text-gray-900">PNG</div>
                  <div className="text-sm text-gray-600">High-resolution image with exact layout</div>
                </div>
              </label>
            </div>
          </div>
        </div>
      </Modal>
    </>
  );
};