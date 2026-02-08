import { jsx as _jsx } from "react/jsx-runtime";
import { useState } from 'react';
import GridLayout, {} from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import {} from '@/types';
import { WidgetContainer } from '@/components/widgets/WidgetContainer';
import { useUpdateDashboard } from '@/hooks/useDashboard';
export const DashboardGrid = ({ dashboardId, widgets, isEditing = false }) => {
    const updateDashboard = useUpdateDashboard(dashboardId);
    const [layouts, setLayouts] = useState(widgets.map((w) => ({
        i: w.id,
        x: w.position.x,
        y: w.position.y,
        w: w.position.w,
        h: w.position.h,
    })));
    const handleLayoutChange = (newLayout) => {
        if (!isEditing)
            return;
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
    return (_jsx(GridLayout, { className: "layout", layout: layouts, cols: 12, rowHeight: 30, width: 1200, onLayoutChange: handleLayoutChange, isDraggable: isEditing, isResizable: isEditing, compactType: "vertical", preventCollision: false, children: widgets.map((widget) => (_jsx("div", { children: _jsx(WidgetContainer, { widget: widget, isEditing: isEditing }) }, widget.id))) }));
};
