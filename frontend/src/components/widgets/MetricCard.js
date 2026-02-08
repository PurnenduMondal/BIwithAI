import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import {} from '@/types';
import { useQuery } from '@tanstack/react-query';
import { widgetApi } from '@/api/widgets';
import { Loader } from '@/components/common/Loader';
import { ArrowUpIcon, ArrowDownIcon } from '@heroicons/react/24/solid';
export const MetricCard = ({ widget }) => {
    const { data, isLoading } = useQuery({
        queryKey: ['widgetData', widget.id],
        queryFn: () => widgetApi.getData(widget.id),
    });
    if (isLoading) {
        return (_jsx("div", { className: "flex items-center justify-center h-full", children: _jsx(Loader, {}) }));
    }
    const value = data?.value || 0;
    const change = data?.change || 0;
    const format = widget.config?.format || 'number';
    const formatValue = (val) => {
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
    return (_jsxs("div", { className: "flex flex-col justify-center h-full", children: [_jsx("div", { className: "text-4xl font-bold text-gray-900", children: formatValue(value) }), change !== 0 && (_jsxs("div", { className: "flex items-center mt-2", children: [change > 0 ? (_jsx(ArrowUpIcon, { className: "w-4 h-4 text-green-500 mr-1" })) : (_jsx(ArrowDownIcon, { className: "w-4 h-4 text-red-500 mr-1" })), _jsxs("span", { className: `text-sm font-medium ${change > 0 ? 'text-green-600' : 'text-red-600'}`, children: [Math.abs(change).toFixed(2), "%"] }), _jsx("span", { className: "text-sm text-gray-500 ml-2", children: "vs last period" })] }))] }));
};
