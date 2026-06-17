import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { useCurrency } from '../../hooks/useCurrency';

export default function MonthlyTrendChart({ data = [] }) {
  const fmt = useCurrency();
  if (!data.length) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400 text-sm">
        Немає даних за вибраний період
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={350}>
      <LineChart data={data} margin={{ top: 10, right: 30, left: 10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="month" tick={{ fontSize: 12 }} />
        <YAxis
          tickFormatter={(v) => fmt(v, true)}
          tick={{ fontSize: 11 }}
          domain={[0, (max) => Math.ceil(max * 1.1)]}
        />
        <Tooltip formatter={(v) => [fmt(v), '']} />
        <Legend />
        <Line
          type="monotone"
          dataKey="income"
          stroke="#10b981"
          strokeWidth={2}
          dot={false}
          name="Доходи"
        />
        <Line
          type="monotone"
          dataKey="expense"
          stroke="#ef4444"
          strokeWidth={2}
          dot={false}
          name="Витрати"
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
