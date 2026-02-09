import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useDataSources, useSyncDataSource, useDeleteDataSource } from '../hooks/useDataSource';
import { Button } from '../components/common/Button';
import { PageLoader } from '../components/common/Loader';
import { Modal } from '../components/common/Modal';
import {
  PlusIcon,
  ArrowPathIcon,
  TrashIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';
import { format } from 'date-fns';

export const DataSourceList = () => {
  const { data: dataSources, isLoading } = useDataSources();
  const syncDataSource = useSyncDataSource();
  const deleteDataSource = useDeleteDataSource();
  
  const [deleteId, setDeleteId] = useState<string | null>(null);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'error':
        return <ExclamationCircleIcon className="w-5 h-5 text-red-500" />;
      case 'syncing':
        return <ArrowPathIcon className="w-5 h-5 text-blue-500 animate-spin" />;
      default:
        return <ClockIcon className="w-5 h-5 text-gray-400" />;
    }
  };

  const handleSync = (id: string) => {
    syncDataSource.mutate(id);
  };

  const handleDelete = () => {
    if (deleteId) {
      deleteDataSource.mutate(deleteId);
      setDeleteId(null);
    }
  };

  if (isLoading) {
    return <PageLoader />;
  }

  return (
    <div className="p-6">
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Data Sources</h1>
            <p className="text-gray-600 mt-1">
              Manage your data connections and uploads
            </p>
          </div>
          <Link to="/data-sources/create">
            <Button>
              <PlusIcon className="w-5 h-5 mr-2" />
              Add Data Source
            </Button>
          </Link>
        </div>
      </div>

      {/* Data Sources Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Last Sync
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {dataSources?.map((ds) => (
              <tr key={ds.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">{ds.name}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                    {ds.type.toUpperCase()}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(ds.status)}
                    <span className="text-sm text-gray-900 capitalize">{ds.status}</span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {ds.last_sync 
                    ? format(new Date(ds.last_sync), 'MMM d, yyyy HH:mm')
                    : 'Never'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <div className="flex items-center justify-end gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleSync(ds.id)}
                      disabled={ds.status === 'syncing'}
                    >
                      <ArrowPathIcon className="w-4 h-4" />
                    </Button>
                    <Link to={`/data-sources/${ds.id}`}>
                      <Button size="sm" variant="outline">
                        View
                      </Button>
                    </Link>
                    <Button
                      size="sm"
                      variant="danger"
                      onClick={() => setDeleteId(ds.id)}
                    >
                      <TrashIcon className="w-4 h-4" />
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {(!dataSources || dataSources.length === 0) && (
          <div className="text-center py-12">
            <p className="text-gray-500">No data sources yet. Add your first data source to get started.</p>
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deleteId}
        onClose={() => setDeleteId(null)}
        title="Delete Data Source"
        footer={
          <>
            <Button variant="outline" onClick={() => setDeleteId(null)}>
              Cancel
            </Button>
            <Button variant="danger" onClick={handleDelete}>
              Delete
            </Button>
          </>
        }
      >
        <p className="text-gray-600">
          Are you sure you want to delete this data source? This action cannot be undone and will affect all dashboards using this data.
        </p>
      </Modal>
    </div>
  );
};