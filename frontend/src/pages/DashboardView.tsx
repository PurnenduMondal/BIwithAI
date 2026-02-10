import { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { useDashboard } from '../hooks/useDashboard';
import { PageLoader } from '../components/common/Loader';
import { DashboardHeader } from '../components/dashboard/DashboardHeader';
import { DashboardGrid } from '../components/dashboard/DashboardGrid';
import { useWebSocket } from '../hooks/useWebSocket';
import toast from 'react-hot-toast';
import type { Widget } from '../types';

export const DashboardView = () => {
  const { id } = useParams<{ id: string }>();
  const { data: dashboard, isLoading } = useDashboard(id!);
  const [isEditing, setIsEditing] = useState(false);
  const [selectedWidget, setSelectedWidget] = useState<Widget | null | undefined>(undefined);
  const { lastMessage, subscribe, unsubscribe } = useWebSocket();
  const saveDashboardRef = useRef<() => Promise<void>>();

  const handleSave = async () => {
    if ((window as any).__saveDashboardChanges) {
      await (window as any).__saveDashboardChanges();
      toast.success('Dashboard changes saved!');
      setIsEditing(false);
    }
  };

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
    <div className="flex flex-col h-screen" data-dashboard-container>
      <DashboardHeader
        dashboard={dashboard}
        onEdit={() => setIsEditing(!isEditing)}
        isEditing={isEditing}
        onAddWidget={() => setSelectedWidget(null)}
        onSave={handleSave}
      />

      <div className="flex-1 overflow-auto p-6" data-dashboard-grid-container>
        <DashboardGrid
          dashboardId={dashboard.id}
          isEditing={isEditing}
          selectedWidget={selectedWidget}
          onSelectWidget={setSelectedWidget}
          onSave={handleSave}
        />
      </div>
    </div>
  );
};