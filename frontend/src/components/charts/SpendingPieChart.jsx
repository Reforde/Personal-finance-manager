import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { useCurrency } from '../../hooks/useCurrency';

const COLORS = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
  '#06b6d4', '#f97316', '#84cc16', '#ec4899', '#6366f1',
];

export default function SpendingPieChart({ data = [] }) {
  const fmt = useCurrency();
  if (!data.length) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400 text-sm">
        Немає витрат за вибраний період
      </div>
    );
  }

  const chartData = data.map((item) => ({
    name: `${item.category?.icon ?? ''} ${item.category?.name ?? 'Без категорії'}`.trim(),
    amount: item.amount,
    percentage: item.percentage,
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={chartData}
          dataKey="amount"
          nameKey="name"
          cx="50%"
          cy="50%"
          outerRadius={100}
          label={({ name, percent }) =>
            percent > 0.04 ? `${(percent * 100).toFixed(0)}%` : ''
          }
          labelLine={false}
        >
          {chartData.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          formatter={(value) => [fmt(value), 'Сума']}
        />
        <Legend
          formatter={(value) => (
            <span className="text-xs text-gray-700">{value}</span>
          )}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
