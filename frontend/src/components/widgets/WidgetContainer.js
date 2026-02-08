import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import {} from '@/types';
import { MetricCard } from './MetricCard';
import { ChartWidget } from './ChartWidget';
import { TableWidget } from './TableWidget';
import { InsightWidget } from './InsightWidget';
import { Cog6ToothIcon, TrashIcon } from '@heroicons/react/24/outline';
export const WidgetContainer = ({ widget, isEditing }) => {
    const renderWidget = () => {
        switch (widget.widget_type) {
            case 'metric':
                return _jsx(MetricCard, { widget: widget });
            case 'chart':
                return _jsx(ChartWidget, { widget: widget });
            case 'table':
                return _jsx(TableWidget, { widget: widget });
            case 'ai_insight':
                return _jsx(InsightWidget, { widget: widget });
            default:
                return _jsx("div", { children: "Unknown widget type" });
        }
    };
    return (_jsxs("div", { className: "h-full bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden", children: [_jsxs("div", { className: "flex items-center justify-between px-4 py-2 border-b border-gray-200 bg-gray-50", children: [_jsx("h3", { className: "font-medium text-gray-900 text-sm", children: widget.title }), isEditing && (_jsxs("div", { className: "flex items-center gap-1", children: [_jsx("button", { className: "p-1 text-gray-400 hover:text-gray-600 rounded", children: _jsx(Cog6ToothIcon, { className: "w-4 h-4" }) }), _jsx("button", { className: "p-1 text-gray-400 hover:text-red-600 rounded", children: _jsx(TrashIcon, { className: "w-4 h-4" }) })] }))] }), _jsx("div", { className: "p-4 h-[calc(100%-48px)]", children: renderWidget() })] }));
};
