import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import {} from '@/types';
import { useQuery } from '@tanstack/react-query';
import { insightApi } from '@/api/insights';
import { Loader } from '@/components/common/Loader';
import { LightBulbIcon } from '@heroicons/react/24/solid';
export const InsightWidget = ({ widget }) => {
    const { data: insights, isLoading } = useQuery({
        queryKey: ['insights', widget.dashboard_id],
        queryFn: () => insightApi.list(widget.dashboard_id),
    });
    if (isLoading) {
        return (_jsx("div", { className: "flex items-center justify-center h-full", children: _jsx(Loader, {}) }));
    }
    return (_jsxs("div", { className: "space-y-3 h-full overflow-y-auto", children: [insights?.slice(0, 5).map((insight) => (_jsx("div", { className: "p-3 bg-blue-50 border border-blue-200 rounded-lg", children: _jsxs("div", { className: "flex items-start gap-2", children: [_jsx(LightBulbIcon, { className: "w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" }), _jsxs("div", { className: "flex-1", children: [_jsx("p", { className: "text-sm font-medium text-gray-900", children: insight.insight_type.replace('_', ' ').toUpperCase() }), _jsx("p", { className: "text-sm text-gray-700 mt-1", children: insight.content }), _jsx("div", { className: "flex items-center gap-2 mt-2", children: _jsxs("span", { className: "text-xs text-gray-500", children: ["Confidence: ", (insight.confidence_score * 100).toFixed(0), "%"] }) })] })] }) }, insight.id))), (!insights || insights.length === 0) && (_jsxs("div", { className: "flex flex-col items-center justify-center h-full text-gray-400", children: [_jsx(LightBulbIcon, { className: "w-12 h-12 mb-2" }), _jsx("p", { className: "text-sm", children: "No insights available yet" })] }))] }));
};
