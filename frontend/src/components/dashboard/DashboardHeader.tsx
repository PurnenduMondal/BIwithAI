import { useState } from 'react';
import { type Dashboard } from '@/types';
import { Button } from '@/components/common/Button';
import { Modal } from '@/components/common/Modal';
import { useDeleteDashboard, useDuplicateDashboard } from '@/hooks/useDashboard';
import { dashboardApi } from '@/api/dashboards';
import toast from 'react-hot-toast';
import {
  PencilIcon,
  TrashIcon,
  DocumentDuplicateIcon,
  ShareIcon,
  ArrowDownTrayIcon,
  PlusIcon,
} from '@heroicons/react/24/outline';

interface DashboardHeaderProps {
  dashboard: Dashboard;
  onEdit: () => void;
  isEditing: boolean;
  onAddWidget?: () => void;
}

export const DashboardHeader = ({ dashboard, onEdit, isEditing, onAddWidget }: DashboardHeaderProps) => {
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
    } catch (error) {
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

          <div className="flex items-center gap-2">
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
            
            <Button
              variant="outline"
              size="sm"
              onClick={onEdit}
            >
              <PencilIcon className="w-4 h-4 mr-2" />
              {isEditing ? 'Done Editing' : 'Edit'}
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
            >
              <ShareIcon className="w-4 h-4 mr-2" />
              Share
            </Button>

            <Button
              variant="outline"
              size="sm"
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
    </>
  );
};