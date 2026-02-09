import { useState, useRef, useEffect } from 'react';
import GridLayout from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import { type Widget } from '../../types';
import { WidgetContainer } from '../widgets/WidgetContainer';
import { WidgetSettingsSidebar } from '../widgets/WidgetSettingsSidebar';
import { apiClient } from '../../api/client';
import { useWidgets } from '../../hooks/useWidget';
import { PageLoader } from '../common/Loader';

interface DashboardGridProps {
  dashboardId: string;
  isEditing?: boolean;
  selectedWidget: Widget | null | undefined;
  onSelectWidget: (widget: Widget | null | undefined) => void;
}

interface LayoutItem {
  i: string;
  x: number;
  y: number;
  w: number;
  h: number;
}

export const DashboardGrid = ({ dashboardId, isEditing = false, selectedWidget, onSelectWidget }: DashboardGridProps) => {
  const { data: widgets, isLoading, error } = useWidgets(dashboardId);
  const [isDragging, setIsDragging] = useState(false);
  const [layouts, setLayouts] = useState<LayoutItem[]>([]);
  
  // Track pending updates
  const pendingUpdates = useRef<Map<string, { x: number; y: number; w: number; h: number }>>(new Map());

  // Update layouts when widgets data changes
  useEffect(() => {
    if (widgets) {
      setLayouts(widgets.map((w) => ({
        i: w.id,
        x: w.position.x,
        y: w.position.y,
        w: w.position.w,
        h: w.position.h,
      })));
    }
  }, [widgets]);

  const handleDragStart = () => {
    setIsDragging(true);
  };

  const handleDragOrResizeStop = (layout: readonly LayoutItem[]) => {
    setIsDragging(false);
    
    if (!widgets) return;
    
    // Update all widgets that have changed position or size
    layout.forEach((item) => {
      const widget = widgets.find(w => w.id === item.i);
      if (widget) {
        const hasChanged = 
          widget.position.x !== item.x ||
          widget.position.y !== item.y ||
          widget.position.w !== item.w ||
          widget.position.h !== item.h;
        
        if (hasChanged) {
          pendingUpdates.current.set(widget.id, {
            x: item.x,
            y: item.y,
            w: item.w,
            h: item.h
          });
        }
      }
    });

    // Execute pending updates
    if (pendingUpdates.current.size > 0) {
      updatePendingWidgets();
    }
  };

  const updatePendingWidgets = async () => {
    if (!widgets) return;
    
    const updates = Array.from(pendingUpdates.current.entries());
    pendingUpdates.current.clear();

    // Update each widget individually
    for (const [widgetId, position] of updates) {
      const widget = widgets.find(w => w.id === widgetId);
      if (widget) {
        try {
          await apiClient.put(`/api/v1/widgets/${widgetId}`, { position });
        } catch (error) {
          console.error(`Failed to update widget ${widgetId}:`, error);
        }
      }
    }
  };

  const handleLayoutChange = (newLayout: readonly LayoutItem[]) => {
    if (!isEditing || isDragging) return;
    setLayouts([...newLayout]);
  };

  if (isLoading) {
    return <PageLoader />;
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <h3 className="text-lg font-medium text-red-600">Error loading widgets</h3>
          <p className="text-gray-600 mt-1">Failed to load dashboard widgets. Please try again.</p>
        </div>
      </div>
    );
  }

  if (!widgets || widgets.length === 0) {
    return (
      <>
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <h3 className="text-lg font-medium text-gray-900">No widgets yet</h3>
            <p className="text-gray-600 mt-1">
              {isEditing ? "Click 'Add Widget' to create your first widget" : "No widgets to display"}
            </p>
          </div>
        </div>

        <WidgetSettingsSidebar
          widget={selectedWidget === undefined ? null : selectedWidget}
          dashboardId={dashboardId}
          isOpen={selectedWidget !== undefined}
          onClose={() => onSelectWidget(undefined)}
        />
      </>
    );
  }

  return (
    <>
      <GridLayout
        className="layout"
        layout={layouts}
        width={1400}
        gridConfig={{
          cols: 12,
          rowHeight: 30,
        }}
        dragConfig={{
          enabled: isEditing,
        }}
        resizeConfig={{
          enabled: isEditing,
        }}
        onLayoutChange={handleLayoutChange}
        onDragStart={handleDragStart}
        onDragStop={handleDragOrResizeStop}
        onResizeStart={handleDragStart}
        onResizeStop={handleDragOrResizeStop}
      >
        {widgets.map((widget) => (
          <div key={widget.id}>
            <WidgetContainer 
              widget={widget} 
              isEditing={isEditing}
              onOpenSettings={onSelectWidget}
            />
          </div>
        ))}
      </GridLayout>

      <WidgetSettingsSidebar
        widget={selectedWidget === undefined ? null : selectedWidget}
        dashboardId={dashboardId}
        isOpen={selectedWidget !== undefined}
        onClose={() => onSelectWidget(undefined)}
      />
    </>
  );
};