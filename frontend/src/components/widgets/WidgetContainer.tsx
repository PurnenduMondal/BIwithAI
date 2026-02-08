import { type Widget } from '@/types';
import { MetricCard } from './MetricCard';
import { ChartWidget } from './ChartWidget';
import { TableWidget } from './TableWidget';
import { InsightWidget } from './InsightWidget';
import { Cog6ToothIcon, TrashIcon } from '@heroicons/react/24/outline';

interface WidgetContainerProps {
  widget: Widget;
  isEditing?: boolean;
}

export const WidgetContainer = ({ widget, isEditing }: WidgetContainerProps) => {
  const renderWidget = () => {
    switch (widget.widget_type) {
      case 'metric':
        return <MetricCard widget={widget} />;
      case 'chart':
        return <ChartWidget widget={widget} />;
      case 'table':
        return <TableWidget widget={widget} />;
      case 'ai_insight':
        return <InsightWidget widget={widget} />;
      default:
        return <div>Unknown widget type</div>;
    }
  };

  return (
    <div className="h-full bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Widget Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200 bg-gray-50">
        <h3 className="font-medium text-gray-900 text-sm">{widget.title}</h3>
        {isEditing && (
          <div className="flex items-center gap-1">
            <button className="p-1 text-gray-400 hover:text-gray-600 rounded">
              <Cog6ToothIcon className="w-4 h-4" />
            </button>
            <button className="p-1 text-gray-400 hover:text-red-600 rounded">
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