import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useDataSource, useSyncDataSource, useDeleteDataSource } from '../hooks/useDataSource';
import { useQuery } from '@tanstack/react-query';
import { dataSourceApi } from '../api/dataSources';
import { Button } from '../components/common/Button';
import { PageLoader } from '../components/common/Loader';
import { Modal } from '../components/common/Modal';
import {
  ArrowLeftIcon,
  ArrowPathIcon,
  TrashIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ClockIcon,
  DocumentChartBarIcon,
  TableCellsIcon,
  CalendarIcon,
} from '@heroicons/react/24/outline';
import { format } from 'date-fns';

export const DataSourceView = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: dataSource, isLoading } = useDataSource(id!);
  const syncDataSource = useSyncDataSource();
  const deleteDataSource = useDeleteDataSource();

  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'schema' | 'preview'>('overview');

  // Fetch schema and preview data
  const { data: schema } = useQuery({
    queryKey: ['dataSourceSchema', id],
    queryFn: () => dataSourceApi.getSchema(id!),
    enabled: !!id && activeTab === 'schema',
  });

  const { data: preview } = useQuery({
    queryKey: ['dataSourcePreview', id],
    queryFn: () => dataSourceApi.preview(id!, 50),
    enabled: !!id && activeTab === 'preview',
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircleIcon className="w-6 h-6 text-green-500" />;
      case 'error':
        return <ExclamationCircleIcon className="w-6 h-6 text-red-500" />;
      case 'syncing':
        return <ArrowPathIcon className="w-6 h-6 text-blue-500 animate-spin" />;
      default:
        return <ClockIcon className="w-6 h-6 text-gray-400" />;
    }
  };

  const handleSync = () => {
    syncDataSource.mutate(id!);
  };

  const handleDelete = () => {
    deleteDataSource.mutate(id!, {
      onSuccess: () => {
        navigate('/data-sources');
      },
    });
  };

  if (isLoading || !dataSource) {
    return <PageLoader />;
  }

  const schemaMetadata = dataSource.schema_metadata || {};
  const columns = schemaMetadata.columns || [];

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/data-sources')}
          className="mb-4"
        >
          <ArrowLeftIcon className="w-4 h-4 mr-2" />
          Back to Data Sources
        </Button>

        <div className="flex items-start justify-between">
          <div className="flex items-start gap-4">
            {getStatusIcon(dataSource.status)}
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{dataSource.name}</h1>
              <div className="flex items-center gap-4 mt-2">
                <span className="px-3 py-1 text-sm font-medium rounded-full bg-blue-100 text-blue-800">
                  {dataSource.type.toUpperCase()}
                </span>
                <span className="text-sm text-gray-500 capitalize">
                  Status: {dataSource.status}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={handleSync}
              disabled={dataSource.status === 'syncing'}
            >
              <ArrowPathIcon className={`w-5 h-5 mr-2 ${dataSource.status === 'syncing' ? 'animate-spin' : ''}`} />
              {dataSource.status === 'syncing' ? 'Syncing...' : 'Sync Now'}
            </Button>
            <Button variant="danger" onClick={() => setShowDeleteModal(true)}>
              <TrashIcon className="w-5 h-5 mr-2" />
              Delete
            </Button>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <TableCellsIcon className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Rows</p>
              <p className="text-2xl font-bold text-gray-900">
                {schemaMetadata.row_count?.toLocaleString() || 'N/A'}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <DocumentChartBarIcon className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Columns</p>
              <p className="text-2xl font-bold text-gray-900">
                {schemaMetadata.total_columns || columns.length || 'N/A'}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <CalendarIcon className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Last Sync</p>
              <p className="text-sm font-medium text-gray-900">
                {dataSource.last_sync 
                  ? format(new Date(dataSource.last_sync), 'MMM d, HH:mm')
                  : 'Never'}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <CheckCircleIcon className="w-6 h-6 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Version</p>
              <p className="text-2xl font-bold text-gray-900">
                {dataSource.last_dataset_version || '1'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px">
            <button
              onClick={() => setActiveTab('overview')}
              className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'overview'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveTab('schema')}
              className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'schema'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Schema
            </button>
            <button
              onClick={() => setActiveTab('preview')}
              className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'preview'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Data Preview
            </button>
          </nav>
        </div>

        <div className="p-6">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Data Source Information</h3>
                <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <dt className="text-sm font-medium text-gray-500">ID</dt>
                    <dd className="mt-1 text-sm text-gray-900 font-mono">{dataSource.id}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Type</dt>
                    <dd className="mt-1 text-sm text-gray-900">{dataSource.type}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Created At</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {format(new Date(dataSource.created_at), 'MMM d, yyyy HH:mm:ss')}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Updated At</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {format(new Date(dataSource.updated_at), 'MMM d, yyyy HH:mm:ss')}
                    </dd>
                  </div>
                </dl>
              </div>

              {columns.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Column Summary</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {columns.slice(0, 6).map((col: any) => (
                      <div key={col.name} className="bg-gray-50 rounded-lg p-4">
                        <p className="font-medium text-gray-900">{col.name}</p>
                        <div className="mt-2 space-y-1">
                          <p className="text-xs text-gray-600">
                            Type: <span className="font-medium">{col.semantic_type || col.data_type}</span>
                          </p>
                          <p className="text-xs text-gray-600">
                            Unique: <span className="font-medium">{col.unique_count}</span>
                          </p>
                          {col.null_percentage !== undefined && (
                            <p className="text-xs text-gray-600">
                              Nulls: <span className="font-medium">{col.null_percentage.toFixed(1)}%</span>
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                  {columns.length > 6 && (
                    <p className="text-sm text-gray-500 mt-4">
                      Showing 6 of {columns.length} columns. View Schema tab for complete details.
                    </p>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Schema Tab */}
          {activeTab === 'schema' && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Data Schema ({columns.length} columns)
              </h3>
              {columns.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Column Name
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Type
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Semantic Type
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                          Unique
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                          Null %
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Stats
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {columns.map((col: any) => (
                        <tr key={col.name} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm font-medium text-gray-900">
                            {col.name}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600">
                            <span className="px-2 py-1 text-xs rounded bg-gray-100">
                              {col.data_type}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600">
                            <span className="px-2 py-1 text-xs rounded bg-blue-100 text-blue-800">
                              {col.semantic_type}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600 text-right">
                            {col.unique_count?.toLocaleString()}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600 text-right">
                            {col.null_percentage?.toFixed(1)}%
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600">
                            {col.min !== undefined && col.max !== undefined && (
                              <span className="text-xs">
                                {typeof col.min === 'number' ? col.min.toFixed(2) : col.min} - 
                                {typeof col.max === 'number' ? col.max.toFixed(2) : col.max}
                              </span>
                            )}
                            {col.top_values && (
                              <span className="text-xs">
                                {Object.keys(col.top_values).length} distinct values
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-gray-500 text-center py-8">No schema information available</p>
              )}
            </div>
          )}

          {/* Preview Tab */}
          {activeTab === 'preview' && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Data Preview (First 50 rows)
              </h3>
              {preview && preview.data && preview.data.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200 text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        {preview.columns.map((col: string) => (
                          <th
                            key={col}
                            className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase whitespace-nowrap"
                          >
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {preview.data.map((row: any, idx: number) => (
                        <tr key={idx} className="hover:bg-gray-50">
                          {preview.columns.map((col: string) => (
                            <td
                              key={col}
                              className="px-4 py-3 text-sm text-gray-900 whitespace-nowrap"
                            >
                              {row[col] !== null && row[col] !== undefined
                                ? String(row[col])
                                : '-'}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-500">Loading preview data...</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        title="Delete Data Source"
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
          Are you sure you want to delete <strong>{dataSource.name}</strong>? 
          This action cannot be undone and will affect all dashboards using this data source.
        </p>
      </Modal>
    </div>
  );
};
