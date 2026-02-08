import { useState } from 'react';
import GridLayout, { type Layout } from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import { type Widget } from '@/types';
import { WidgetContainer } from '@/components/widgets/WidgetContainer';
import { useUpdateDashboard } from '@/hooks/useDashboard';

interface DashboardGridProps {
  dashboardId: string;
  widgets: Widget[];
  isEditing?: boolean;
}

export const DashboardGrid = ({ dashboardId, widgets, isEditing = false }: DashboardGridProps) => {
  const updateDashboard = useUpdateDashboard(dashboardId);
  const [layouts, setLayouts] = useState<Layout[]>(
    widgets.map((w) => ({
      i: w.id,
      x: w.position.x,
      y: w.position.y,
      w: w.position.w,
      h: w.position.h,
    }))
  );

  const handleLayoutChange = (newLayout: Layout[]) => {
    if (!isEditing) return;

    setLayouts(newLayout);

    // Update widget positions in the backend
    const updatedWidgets = widgets.map((widget) => {
      const layout = newLayout.find((l) => l.i === widget.id);
      if (layout) {
        return {
          ...widget,
          position: {
            x: layout.x,
            y: layout.y,
            w: layout.w,
            h: layout.h,
          },
        };
      }
      return widget;
    });

    // You might want to debounce this
    updateDashboard.mutate({
      layout_config: { widgets: updatedWidgets },
    });
  };

  return (
    <GridLayout
      className="layout"
      layout={layouts}
      cols={12}
      rowHeight={30}
      width={1200}
      onLayoutChange={handleLayoutChange}
      isDraggable={isEditing}
      isResizable={isEditing}
      compactType="vertical"
      preventCollision={false}
    >
      {widgets.map((widget) => (
        <div key={widget.id}>
          <WidgetContainer widget={widget} isEditing={isEditing} />
        </div>
      ))}
    </GridLayout>
  );
};