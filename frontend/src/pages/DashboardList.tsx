import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useDashboards } from '@/hooks/useDashboard';
import { Button } from '@/components/common/Button';
import { Loader, PageLoader } from '@/components/common/Loader';
import { Modal } from '@/components/common/Modal';
import { useDataSources } from '@/hooks/useDataSource';
import { useGenerateDashboard } from '@/hooks/useDashboard';
import {
  PlusIcon,
  ChartBarIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';
import { format } from 'date-fns';

export const DashboardList = () => {
  const { data: dashboards, isLoading } = useDashboards();
  const { data: dataSources } = useDataSources();
  const generateDashboard = useGenerateDashboard();
  
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedDataSource, setSelectedDataSource] = useState('');

  const handleGenerateDashboard = () => {
    if (!selectedDataSource) return;
    
    generateDashboard.mutate({
      data_source_id: selectedDataSource,
      preferences: {},
    });
    setShowCreateModal(false);
  };

  if (isLoading) {
    return <PageLoader />;
  }

  return (
    <div className="p-6">
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Dashboards</h1>
            <p className="text-gray-600 mt-1">
              Manage and view your business intelligence dashboards
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center"
            >
              <SparklesIcon className="w-5 h-5 mr-2" />
              Auto-Generate Dashboard
            </Button>
            <Link to="/dashboards/create">
              <Button variant="outline">
                <PlusIcon className="w-5 h-5 mr-2" />
                Create Blank Dashboard
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Dashboard Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {dashboards?.map((dashboard) => (
          <Link
            key={dashboard.id}
            to={`/dashboards/${dashboard.id}`}
            className="block"
          >
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow overflow-hidden">
              {/* Dashboard Preview */}
              <div className="h-48 bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
                <ChartBarIcon className="w-16 h-16 text-white opacity-50" />
              </div>

              {/* Dashboard Info */}
              <div className="p-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  {dashboard.name}
                </h3>
                {dashboard.description && (
                  <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                    {dashboard.description}
                  </p>
                )}
                <div className="flex items-center justify-between mt-4 text-xs text-gray-500">
                  <span>
                    Updated {format(new Date(dashboard.updated_at), 'MMM d, yyyy')}
                  </span>
                  <span className="flex items-center gap-1">
                    {dashboard.widgets?.length || 0} widgets
                  </span>
                </div>
              </div>
            </div>
          </Link>
        ))}

        {/* Empty State */}
        {(!dashboards || dashboards.length === 0) && (
          <div className="col-span-full">
            <div className="text-center py-12">
              <ChartBarIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No dashboards</h3>
              <p className="mt-1 text-sm text-gray-500">
                Get started by creating a new dashboard or auto-generating one from your data.
              </p>
              <div className="mt-6 flex justify-center gap-4">
                <Button onClick={() => setShowCreateModal(true)}>
                  <SparklesIcon className="w-5 h-5 mr-2" />
                  Auto-Generate Dashboard
                </Button>
                <Link to="/dashboards/create">
                  <Button variant="outline">
                    <PlusIcon className="w-5 h-5 mr-2" />
                    Create Blank Dashboard
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Auto-Generate Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Auto-Generate Dashboard"
        footer={
          <>
            <Button variant="outline" onClick={() => setShowCreateModal(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleGenerateDashboard}
              disabled={!selectedDataSource}
              isLoading={generateDashboard.isPending}
            >
              Generate Dashboard
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            Select a data source to automatically generate a dashboard with relevant widgets and insights.
          </p>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Data Source
            </label>
            <select
              value={selectedDataSource}
              onChange={(e) => setSelectedDataSource(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select a data source...</option>
              {dataSources?.map((ds) => (
                <option key={ds.id} value={ds.id}>
                  {ds.name} ({ds.type})
                </option>
              ))}
            </select>
          </div>

          {!dataSources || dataSources.length === 0 ? (
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-800">
                No data sources available. Please{' '}
                <Link to="/data-sources/create" className="font-medium underline">
                  create a data source
                </Link>{' '}
                first.
              </p>
            </div>
          ) : null}
        </div>
      </Modal>
    </div>
  );
};