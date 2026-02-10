import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { useExports } from '../../contexts/ExportContext';
import { apiClient } from '../../api/client';
import { ArrowDownTrayIcon, CheckCircleIcon, XCircleIcon, TrashIcon } from '@heroicons/react/24/outline';
import { formatDistanceToNow } from 'date-fns';
import toast from 'react-hot-toast';

interface ExportQueueModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ExportQueueModal = ({ isOpen, onClose }: ExportQueueModalProps) => {
  const { exports, removeExport, clearCompleted } = useExports();

  const handleDownload = async (url: string, filename: string) => {
    try {
      // Fetch file through authenticated API client
      const response = await apiClient.get(url, {
        responseType: 'blob'
      });
      
      // Create blob and download
      const blob = new Blob([response.data]);
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
      
      toast.success('Download started');
    } catch (error) {
      console.error('Download error:', error);
      toast.error('Failed to download file');
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Export Queue"
      footer={
        exports.length > 0 && (
          <Button variant="outline" onClick={clearCompleted}>
            Clear Completed
          </Button>
        )
      }
    >
      <div className="space-y-3">
        {exports.length === 0 ? (
          <div className="text-center py-12">
            <ArrowDownTrayIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">No exports yet</p>
            <p className="text-sm text-gray-400 mt-1">
              Export a dashboard to see it here
            </p>
          </div>
        ) : (
          exports.map((exportJob) => (
            <div
              key={exportJob.jobId}
              className="flex items-center gap-4 p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              {/* Progress Indicator */}
              <div className="flex-shrink-0">
                {exportJob.status === 'completed' ? (
                  <CheckCircleIcon className="w-10 h-10 text-green-500" />
                ) : exportJob.status === 'failed' ? (
                  <XCircleIcon className="w-10 h-10 text-red-500" />
                ) : (
                  <div className="relative w-10 h-10">
                    {/* Background circle */}
                    <svg className="w-10 h-10 transform -rotate-90">
                      <circle
                        cx="20"
                        cy="20"
                        r="16"
                        stroke="currentColor"
                        strokeWidth="3"
                        fill="none"
                        className="text-gray-200"
                      />
                      {/* Progress circle */}
                      <circle
                        cx="20"
                        cy="20"
                        r="16"
                        stroke="currentColor"
                        strokeWidth="3"
                        fill="none"
                        strokeDasharray={`${2 * Math.PI * 16}`}
                        strokeDashoffset={`${2 * Math.PI * 16 * (1 - exportJob.progress / 100)}`}
                        className="text-blue-600 transition-all duration-500"
                        strokeLinecap="round"
                      />
                    </svg>
                    {/* Percentage text */}
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-xs font-semibold text-gray-700">
                        {exportJob.progress}%
                      </span>
                    </div>
                  </div>
                )}
              </div>

              {/* Export Details */}
              <div className="flex-1 min-w-0">
                <h4 className="font-medium text-gray-900 truncate">
                  {exportJob.dashboardName}
                </h4>
                <p className="text-sm text-gray-600 mt-0.5">
                  {exportJob.message || exportJob.status}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-gray-500 uppercase font-medium">
                    {exportJob.format}
                  </span>
                  <span className="text-xs text-gray-400">•</span>
                  <span className="text-xs text-gray-500">
                    {formatDistanceToNow(exportJob.createdAt, { addSuffix: true })}
                  </span>
                </div>
                {exportJob.error && (
                  <p className="text-sm text-red-600 mt-1">{exportJob.error}</p>
                )}
              </div>

              {/* Actions */}
              <div className="flex-shrink-0 flex items-center gap-2">
                {exportJob.status === 'completed' && exportJob.downloadUrl && (
                  <Button
                    size="sm"
                    onClick={() => handleDownload(exportJob.downloadUrl!, `${exportJob.dashboardName}.${exportJob.format}`)}
                  >
                    <ArrowDownTrayIcon className="w-4 h-4 mr-1" />
                    Download
                  </Button>
                )}
                {(exportJob.status === 'completed' || exportJob.status === 'failed') && (
                  <button
                    onClick={() => removeExport(exportJob.jobId)}
                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    title="Remove"
                  >
                    <TrashIcon className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </Modal>
  );
};
