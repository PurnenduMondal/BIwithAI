import { type Widget } from '../../types';
import { useQuery } from '@tanstack/react-query';
import { widgetApi } from '../../api/widgets';
import { Loader } from '../common/Loader';
import { LineChart } from '../charts/LineChart';
import { BarChart } from '../charts/BarChart';
import { PieChart } from '../charts/PieChart';
import { AreaChart } from '../charts/AreaChart';
import { ScatterChart } from '../charts/ScatterChart';

interface ChartWidgetProps {
  widget: Widget;
  data?: any[]; // Optional data for preview mode (chat)
}

export const ChartWidget = ({ widget, data: previewData }: ChartWidgetProps) => {
  const { data: fetchedData, isLoading } = useQuery({
    queryKey: ['widgetData', widget.id],
    queryFn: () => widgetApi.getData(widget.id),
    enabled: !previewData, // Skip query if preview data provided
    staleTime: 0, // Always consider data stale
    refetchOnMount: true, // Refetch when component mounts
  });

  if (!previewData && isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader />
      </div>
    );
  }

  const chartData = previewData || fetchedData?.data || [];
  const chartConfig = { ...widget.chart_config, ...widget.query_config };

  const renderChart = () => {
    switch (widget.widget_type) {
      case 'line':
        return <LineChart data={chartData} config={chartConfig} />;
      case 'bar':
        return <BarChart data={chartData} config={chartConfig} />;
      case 'pie':
        return <PieChart data={chartData} config={chartConfig} />;
      case 'area':
        return <AreaChart data={chartData} config={chartConfig} />;
      case 'scatter':
        return <ScatterChart data={chartData} config={chartConfig} />;
      case 'heatmap':
        // TODO: Create HeatmapChart component
        return (
          <div className="flex items-center justify-center h-full text-gray-400">
            <p className="text-sm">Heatmap chart coming soon</p>
          </div>
        );
      default:
        return (
          <div className="flex items-center justify-center h-full text-gray-400">
            <p className="text-sm">Unsupported chart type: {widget.widget_type}</p>
          </div>
        );
    }
  };

  return <div className="h-full">{renderChart()}</div>;
};