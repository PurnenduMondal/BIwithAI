import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { PieChart as RechartsPieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer, } from 'recharts';
const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];
export const PieChart = ({ data, config }) => {
    const nameKey = config?.name_key || 'name';
    const valueKey = config?.value_key || 'value';
    return (_jsx(ResponsiveContainer, { width: "100%", height: "100%", children: _jsxs(RechartsPieChart, { children: [_jsx(Pie, { data: data, dataKey: valueKey, nameKey: nameKey, cx: "50%", cy: "50%", outerRadius: 80, label: true, children: data.map((entry, index) => (_jsx(Cell, { fill: COLORS[index % COLORS.length] }, `cell-${index}`))) }), _jsx(Tooltip, {}), _jsx(Legend, {})] }) }));
};
