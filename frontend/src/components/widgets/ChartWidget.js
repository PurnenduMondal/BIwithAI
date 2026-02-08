import { jsx as _jsx } from "react/jsx-runtime";
import {} from '@/types';
import { useQuery } from '@tanstack/react-query';
import { widgetApi } from '@/api/widgets';
import { Loader } from '@/components/common/Loader';
import { LineChart } from '@/components/charts/LineChart';
import { BarChart } from '@/components/charts/BarChart';
import { PieChart } from '@/components/charts/PieChart';
import { AreaChart } from '@/components/charts/AreaChart';
export const ChartWidget = ({ widget }) => {
    const { data, isLoading } = useQuery({
        queryKey: ['widgetData', widget.id],
        queryFn: () => widgetApi.getData(widget.id),
    });
    if (isLoading) {
        return (_jsx("div", { className: "flex items-center justify-center h-full", children: _jsx(Loader, {}) }));
    }
    const chartType = widget.config?.chart_type || 'line';
    const chartData = data?.data || [];
    const renderChart = () => {
        switch (chartType) {
            case 'line':
                return _jsx(LineChart, { data: chartData, config: widget.config });
            case 'bar':
                return _jsx(BarChart, { data: chartData, config: widget.config });
            case 'pie':
                return _jsx(PieChart, { data: chartData, config: widget.config });
            case 'area':
                return _jsx(AreaChart, { data: chartData, config: widget.config });
            default:
                return _jsx("div", { children: "Unsupported chart type" });
        }
    };
    return _jsx("div", { className: "h-full", children: renderChart() });
};
