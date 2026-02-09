import { type Widget } from '../../types';
import { useQuery } from '@tanstack/react-query';
import { widgetApi } from '../../api/widgets';
import { Loader } from '../common/Loader';
import { ArrowUpIcon, ArrowDownIcon } from '@heroicons/react/24/solid';

interface MetricCardProps {
  widget: Widget;
}

export const MetricCard = ({ widget }: MetricCardProps) => {
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

  const value = data?.value || 0;
  const change = data?.change || 0;
  const format = widget.config?.format || 'number';
  const comparisonPeriod = widget.config?.comparison_period;

  const formatValue = (val: number) => {
    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
        }).format(val);
      case 'percentage':
        return `${val.toFixed(2)}%`;
      default:
        return val.toLocaleString();
    }
  };

  const getPeriodLabel = () => {
    switch (comparisonPeriod) {
      case 'previous_week':
        return 'vs previous week';
      case 'previous_month':
        return 'vs previous month';
      case 'previous_quarter':
        return 'vs previous quarter';
      case 'previous_year':
        return 'vs previous year';
      default:
        return 'vs last period';
    }
  };

  return (
    <div className="flex flex-col justify-center h-full">
      <div className="text-4xl font-bold text-gray-900">
        {formatValue(value)}
      </div>
      
      {change !== 0 && (
        <div className="flex items-center mt-2">
          {change > 0 ? (
            <ArrowUpIcon className="w-4 h-4 text-green-500 mr-1" />
          ) : (
            <ArrowDownIcon className="w-4 h-4 text-red-500 mr-1" />
          )}
          <span
            className={`text-sm font-medium ${
              change > 0 ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {Math.abs(change).toFixed(2)}%
          </span>
          <span className="text-sm text-gray-500 ml-2">{getPeriodLabel()}</span>
        </div>
      )}
    </div>
  );
};