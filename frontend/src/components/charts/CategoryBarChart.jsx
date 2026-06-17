import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell,
} from 'recharts';
import { useCurrency } from '../../hooks/useCurrency';

const COLORS = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
  '#06b6d4', '#f97316', '#84cc16', '#ec4899', '#6366f1',
];

export default function CategoryBarChart({ data = [] }) {
  const fmt = useCurrency();
  if (!data.length) {
    return (
      <div className="flex items-center justify-center h-48 text-gray-400 text-sm">
        Немає витрат за вибраний період
      </div>
    );
  }

  const chartData = data.map((item) => ({
    name: `${item.category?.icon ?? ''} ${item.category?.name ?? 'Без категорії'}`.trim(),
    amount: item.amount,
  }));

  return (
    <ResponsiveContainer width="100%" height={Math.max(chartData.length * 42, 200)}>
      <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 24 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
        <XAxis
          type="number"
          tickFormatter={(v) => fmt(v, true)}
          tick={{ fontSize: 11 }}
        />
        <YAxis
          type="category"
          dataKey="name"
          width={130}
          tick={{ fontSize: 12 }}
        />
        <Tooltip formatter={(v) => [fmt(v), 'Витрати']} />
        <Bar dataKey="amount" radius={[0, 4, 4, 0]}>
          {chartData.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
