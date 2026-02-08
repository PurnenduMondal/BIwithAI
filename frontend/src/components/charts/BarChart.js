import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { BarChart as RechartsBarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, } from 'recharts';
export const BarChart = ({ data, config }) => {
    const xAxis = config?.x_axis || 'category';
    const yAxis = config?.y_axis || 'value';
    return (_jsx(ResponsiveContainer, { width: "100%", height: "100%", children: _jsxs(RechartsBarChart, { data: data, children: [_jsx(CartesianGrid, { strokeDasharray: "3 3", stroke: "#e5e7eb" }), _jsx(XAxis, { dataKey: xAxis, stroke: "#6b7280", style: { fontSize: '12px' } }), _jsx(YAxis, { stroke: "#6b7280", style: { fontSize: '12px' } }), _jsx(Tooltip, { contentStyle: {
                        backgroundColor: '#fff',
                        border: '1px solid #e5e7eb',
                        borderRadius: '8px',
                    } }), _jsx(Legend, {}), _jsx(Bar, { dataKey: yAxis, fill: "#3b82f6", radius: [8, 8, 0, 0] })] }) }));
};
