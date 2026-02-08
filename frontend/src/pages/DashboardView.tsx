import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useDashboard } from '@/hooks/useDashboard';
import { useCreateWidget } from '@/hooks/useWidget';
import { PageLoader } from '@/components/common/Loader';
import { DashboardHeader } from '@/components/dashboard/DashboardHeader';
import { DashboardGrid } from '@/components/dashboard/DashboardGrid';
import { CreateWidgetModal } from '@/components/widgets/CreateWidgetModal';
import { useWebSocket } from '@/hooks/useWebSocket';
import toast from 'react-hot-toast';
import type { CreateWidgetData } from '@/api/widgets';

export const DashboardView = () => {
  const { id } = useParams<{ id: string }>();
  const { data: dashboard, isLoading } = useDashboard(id!);
  const createWidget = useCreateWidget(id!);
  const [isEditing, setIsEditing] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const { lastMessage, subscribe, unsubscribe } = useWebSocket();

  // Subscribe to dashboard updates via WebSocket
  useEffect(() => {
    if (id) {
      subscribe('dashboard', id);
      return () => unsubscribe('dashboard', id);
    }
  }, [id, subscribe, unsubscribe]);

  // Handle WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      if (lastMessage.type === 'dashboard_updated') {
        toast.success('Dashboard updated in real-time!');
        // Optionally refetch data
      } else if (lastMessage.type === 'datasource_updated') {
        toast.success('Data source updated!');
      }
    }
  }, [lastMessage]);

  const handleCreateWidget = (widgetData: CreateWidgetData) => {
    createWidget.mutate(widgetData);
  };

  if (isLoading) {
    return <PageLoader />;
  }

  if (!dashboard) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900">Dashboard not found</h2>
          <p className="text-gray-600 mt-2">The dashboard you're looking for doesn't exist.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen">
      <DashboardHeader
        dashboard={dashboard}
        onEdit={() => setIsEditing(!isEditing)}
        isEditing={isEditing}
        onAddWidget={() => setShowCreateModal(true)}
      />

      <div className="flex-1 overflow-auto p-6">
        {dashboard.widgets && dashboard.widgets.length > 0 ? (
          <DashboardGrid
            dashboardId={dashboard.id}
            widgets={dashboard.widgets}
            isEditing={isEditing}
          />
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <h3 className="text-lg font-medium text-gray-900">No widgets yet</h3>
              <p className="text-gray-600 mt-1">
                {isEditing 
                  ? 'Click the add button to create your first widget'
                  : 'Enable edit mode to add widgets to your dashboard'}
              </p>
            </div>
          </div>
        )}
      </div>

      <CreateWidgetModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSubmit={handleCreateWidget}
        isLoading={createWidget.isPending}
      />
    </div>
  );
};