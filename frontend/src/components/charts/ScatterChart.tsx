import {
  ScatterChart as RechartsScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ZAxis,
} from 'recharts';

interface ScatterChartProps {
  data: any[];
  config?: Record<string, any>;
}

export const ScatterChart = ({ data, config }: ScatterChartProps) => {
  const xAxis = config?.x_axis || 'x';
  const yAxis = config?.y_axis || 'y';
  const zAxis = config?.z_axis; // Optional size dimension
  const colors = config?.colors || ['#3b82f6'];

  return (
    <ResponsiveContainer width="100%" height="100%">
      <RechartsScatterChart>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis
          type="number"
          dataKey={xAxis}
          name={xAxis}
          stroke="#6b7280"
          style={{ fontSize: '12px' }}
        />
        <YAxis
          type="number"
          dataKey={yAxis}
          name={yAxis}
          stroke="#6b7280"
          style={{ fontSize: '12px' }}
        />
        {zAxis && (
          <ZAxis
            type="number"
            dataKey={zAxis}
            range={[60, 400]}
            name={zAxis}
          />
        )}
        <Tooltip
          cursor={{ strokeDasharray: '3 3' }}
          contentStyle={{
            backgroundColor: '#fff',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
          }}
        />
        <Legend />
        <Scatter
          name={`${xAxis} vs ${yAxis}`}
          data={data}
          fill={colors[0]}
        />
      </RechartsScatterChart>
    </ResponsiveContainer>
  );
};
