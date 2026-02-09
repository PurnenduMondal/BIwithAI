import {
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

interface PieChartProps {
  data: any[];
  config?: Record<string, any>;
}

export const PieChart = ({ data, config }: PieChartProps) => {
  const xAxis = config?.x_axis || 'name';
  const yAxis = config?.y_axis || 'value';

  // Transform data to handle string values (like "25.50%")
  const transformedData = data.map(item => {
    const value = item[yAxis];
    let numericValue = value;
    let displayValue = value;

    // If value is a string, try to parse it
    if (typeof value === 'string') {
      // Remove % sign and parse
      const cleaned = value.replace('%', '').trim();
      const parsed = parseFloat(cleaned);
      if (!isNaN(parsed)) {
        numericValue = parsed;
        displayValue = value; // Keep original formatted string
      }
    }

    return {
      ...item,
      [yAxis]: numericValue,
      [`${yAxis}_display`]: displayValue,
    };
  });

  // Custom label to show the formatted value
  const renderLabel = (entry: any) => {
    const displayValue = entry[`${yAxis}_display`];
    return displayValue !== undefined ? displayValue : entry[yAxis];
  };

  // Custom tooltip to show formatted value
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const displayValue = data[`${yAxis}_display`];
      return (
        <div className="bg-white p-2 border border-gray-300 rounded shadow-sm">
          <p className="font-medium">{data[xAxis]}</p>
          <p className="text-sm text-gray-600">
            {displayValue !== undefined ? displayValue : payload[0].value}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <ResponsiveContainer width="100%" height="100%">
      <RechartsPieChart>
        <Pie
          data={transformedData}
          dataKey={yAxis}
          nameKey={xAxis}
          cx="50%"
          cy="50%"
          outerRadius={80}
          label={renderLabel}
        >
          {transformedData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        <Legend />
      </RechartsPieChart>
    </ResponsiveContainer>
  );
};