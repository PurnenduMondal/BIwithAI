import { type Widget } from '../../types';
import { MetricCard } from './MetricCard';
import { ChartWidget } from './ChartWidget';
import { TableWidget } from './TableWidget';
import { InsightWidget } from './InsightWidget';
import { Cog6ToothIcon, TrashIcon } from '@heroicons/react/24/outline';
import { useDeleteWidget } from '../../hooks/useWidget';

interface WidgetContainerProps {
  widget: Widget;
  isEditing?: boolean;
  onOpenSettings?: (widget: Widget) => void;
}

export const WidgetContainer = ({ widget, isEditing, onOpenSettings }: WidgetContainerProps) => {
  const deleteWidget = useDeleteWidget();

  const handleDelete = () => {
    if (window.confirm(`Are you sure you want to delete "${widget.title}"?`)) {
      deleteWidget.mutate(widget.id);
    }
  };

  const renderWidget = () => {
    // Chart types that use ChartWidget component
    const chartTypes = ['line', 'bar', 'pie', 'area', 'scatter', 'heatmap'];
    
    if (chartTypes.includes(widget.widget_type)) {
      return <ChartWidget widget={widget} />;
    }
    
    switch (widget.widget_type) {
      case 'metric':
      case 'gauge':
        return <MetricCard widget={widget} />;
      case 'table':
        return <TableWidget widget={widget} />;
      default:
        return (
          <div className="flex items-center justify-center h-full text-gray-400">
            <div className="text-center">
              <p className="text-sm">Unsupported widget type: {widget.widget_type}</p>
              {widget.ai_reasoning && (
                <p className="text-xs mt-2 text-gray-500 italic">{widget.ai_reasoning}</p>
              )}
            </div>
          </div>
        );
    }
  };

  return (
    <div className="h-full bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Widget Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200 bg-gray-50">
        <h3 className="font-medium text-gray-900 text-sm">{widget.title}</h3>
        {isEditing && (
          <div className="flex items-center gap-1">
            <button 
              className="p-1 text-gray-400 hover:text-gray-600 rounded"
              onClick={() => onOpenSettings?.(widget)}
              title="Widget settings"
            >
              <Cog6ToothIcon className="w-4 h-4" />
            </button>
            <button 
              className="p-1 text-gray-400 hover:text-red-600 rounded"
              onClick={handleDelete}
              title="Delete widget"
            >
              <TrashIcon className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* Widget Content */}
      <div className="p-4 h-[calc(100%-48px)]">
        {renderWidget()}
      </div>
    </div>
  );
};