import { type Widget } from '../../types';
import { useQuery } from '@tanstack/react-query';
import { widgetApi } from '../../api/widgets';
import { Loader } from '../common/Loader';
import { LineChart } from '../charts/LineChart';
import { BarChart } from '../charts/BarChart';
import { PieChart } from '../charts/PieChart';
import { AreaChart } from '../charts/AreaChart';

interface ChartWidgetProps {
  widget: Widget;
}

export const ChartWidget = ({ widget }: ChartWidgetProps) => {
  const { data, isLoading } = useQuery({
    queryKey: ['widgetData', widget.id],
    queryFn: () => widgetApi.getData(widget.id),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader />
      </div>
    );
  }

  const chartType = widget.config?.chart_type || 'line';
  const chartData = data?.data || [];

  const renderChart = () => {
    switch (chartType) {
      case 'line':
        return <LineChart data={chartData} config={widget.config} />;
      case 'bar':
        return <BarChart data={chartData} config={widget.config} />;
      case 'pie':
        return <PieChart data={chartData} config={widget.config} />;
      case 'area':
        return <AreaChart data={chartData} config={widget.config} />;
      default:
        return <div>Unsupported chart type</div>;
    }
  };

  return <div className="h-full">{renderChart()}</div>;
};