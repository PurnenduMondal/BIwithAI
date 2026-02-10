import { type Widget } from '../../types';
import { useQuery } from '@tanstack/react-query';
import { widgetApi } from '../../api/widgets';
import { Loader } from '../common/Loader';
import { ArrowUpIcon, ArrowDownIcon } from '@heroicons/react/24/solid';

interface MetricCardProps {
  widget: Widget;
  data?: any; // Optional data for preview mode (chat)
}

export const MetricCard = ({ widget, data: previewData }: MetricCardProps) => {
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

  const responseData = previewData || fetchedData;
  const value = responseData?.value || 0;
  const chartConfig = widget.chart_config || {};
  const format = chartConfig?.format || 'number';
  const prefix = chartConfig?.prefix || '';
  const suffix = chartConfig?.suffix || '';
    
  // For gauge type, get min/max values
  const isGauge = widget.widget_type === 'gauge';
  const minValue = chartConfig?.min_value || 0;
  const maxValue = chartConfig?.max_value || 100;
  const percentage = isGauge ? ((value - minValue) / (maxValue - minValue)) * 100 : 0;

  const formatValue = (val: number) => {
    let displayValue = val;
    
    // Check if this is a percentage stored as decimal (0.156 = 15.6%)
    // If suffix is '%' or format is 'percentage', and value is between 0 and 1 (exclusive)
    const isPercentageFormat = suffix === '%' || format === 'percentage';
    const isDecimalFraction = val > 0 && val < 1;
    
    if (isPercentageFormat && isDecimalFraction) {
      // Convert decimal to percentage (0.156 -> 15.6)
      displayValue = val * 100;
    }
    
    let formattedVal = '';
    
    // If custom prefix/suffix are provided, use them
    if (prefix || suffix) {
      formattedVal = displayValue.toLocaleString(undefined, { 
        minimumFractionDigits: 0,
        maximumFractionDigits: 2 
      });
      return `${prefix}${formattedVal}${suffix}`;
    }
    
    // Otherwise use the format
    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
        }).format(displayValue);
      case 'percentage':
        return `${displayValue.toFixed(2)}%`;
      default:
        return displayValue.toLocaleString();
    }
  };

  return (
    <div className="flex flex-col justify-center h-full">
      {isGauge && (
        <div className="mb-4">
          <div className="relative h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`absolute h-full rounded-full transition-all ${
                percentage >= 80 ? 'bg-green-500' :
                percentage >= 50 ? 'bg-yellow-500' :
                'bg-red-500'
              }`}
              style={{ width: `${Math.min(Math.max(percentage, 0), 100)}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>{formatValue(minValue)}</span>
            <span>{formatValue(maxValue)}</span>
          </div>
        </div>
      )}
      
      <div className="text-4xl font-bold text-gray-900">
        {formatValue(value)}
      </div>
    </div>
  );
};