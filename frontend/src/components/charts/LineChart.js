import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { LineChart as RechartsLineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, } from 'recharts';
export const LineChart = ({ data, config }) => {
    const xAxis = config?.x_axis || 'date';
    const yAxis = config?.y_axis || 'value';
    return (_jsx(ResponsiveContainer, { width: "100%", height: "100%", children: _jsxs(RechartsLineChart, { data: data, children: [_jsx(CartesianGrid, { strokeDasharray: "3 3", stroke: "#e5e7eb" }), _jsx(XAxis, { dataKey: xAxis, stroke: "#6b7280", style: { fontSize: '12px' } }), _jsx(YAxis, { stroke: "#6b7280", style: { fontSize: '12px' } }), _jsx(Tooltip, { contentStyle: {
                        backgroundColor: '#fff',
                        border: '1px solid #e5e7eb',
                        borderRadius: '8px',
                    } }), _jsx(Legend, {}), _jsx(Line, { type: "monotone", dataKey: yAxis, stroke: "#3b82f6", strokeWidth: 2, dot: { fill: '#3b82f6', r: 4 }, activeDot: { r: 6 } })] }) }));
};
