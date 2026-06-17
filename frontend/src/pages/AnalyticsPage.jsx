import { useEffect, useState, useCallback } from 'react';
import { format } from 'date-fns';
import client from '../api/client';
import { useCurrency } from '../hooks/useCurrency';
import SpendingPieChart from '../components/charts/SpendingPieChart';
import CategoryBarChart from '../components/charts/CategoryBarChart';
import MonthlyTrendChart from '../components/charts/MonthlyTrendChart';
import SpendingHeatmap from '../components/charts/SpendingHeatmap';

const TABS = [
  { id: 'categories', label: 'Категорії' },
  { id: 'trend',      label: 'Динаміка' },
  { id: 'heatmap',    label: 'Теплова карта' },
];

const today = format(new Date(), 'yyyy-MM-dd');
const monthStart = format(new Date(new Date().getFullYear(), new Date().getMonth(), 1), 'yyyy-MM-dd');

export default function AnalyticsPage() {
  const [tab, setTab] = useState('categories');
  const [from, setFrom] = useState(monthStart);
  const [to, setTo] = useState(today);
  const [trendMonths, setTrendMonths] = useState(12);
  const [heatmapMonth, setHeatmapMonth] = useState(format(new Date(), 'yyyy-MM'));

  const [spending, setSpending] = useState([]);
  const [trend, setTrend] = useState([]);
  const [heatmap, setHeatmap] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchCategories = useCallback(() => {
    setLoading(true);
    client.get(`/analytics/spending-by-category?from=${from}T00:00:00&to=${to}T23:59:59`)
      .then((r) => setSpending(r.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [from, to]);

  const fetchTrend = useCallback(() => {
    setLoading(true);
    client.get(`/analytics/monthly-trend?months=${trendMonths}`)
      .then((r) => setTrend(r.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [trendMonths]);

  const fetchHeatmap = useCallback(() => {
    setLoading(true);
    client.get(`/analytics/daily-heatmap?month=${heatmapMonth}`)
      .then((r) => setHeatmap(r.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [heatmapMonth]);

  useEffect(() => {
    if (tab === 'categories') fetchCategories();
    if (tab === 'trend')      fetchTrend();
    if (tab === 'heatmap')    fetchHeatmap();
  }, [tab, fetchCategories, fetchTrend, fetchHeatmap]);

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-5">
      <h1 className="text-2xl font-bold text-gray-900">Аналітика</h1>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 p-1 rounded-xl w-fit">
        {TABS.map(({ id, label }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              tab === id
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Controls per tab */}
      {tab !== 'heatmap' && tab !== 'trend' && (
        <div className="flex flex-wrap gap-3 items-end bg-white border border-gray-200 rounded-2xl p-4">
          <DateField label="Від" value={from} onChange={setFrom} />
          <DateField label="До"  value={to}   onChange={setTo} />
          <button
            onClick={fetchCategories}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors self-end"
          >
            Оновити
          </button>
        </div>
      )}

      {tab === 'trend' && (
        <div className="flex items-end gap-3 bg-white border border-gray-200 rounded-2xl p-4">
          <div>
            <label className="block text-xs text-gray-500 font-medium mb-1">Місяців</label>
            <select
              value={trendMonths}
              onChange={(e) => setTrendMonths(parseInt(e.target.value))}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
            >
              {[3, 6, 12, 24].map((n) => (
                <option key={n} value={n}>{n} місяців</option>
              ))}
            </select>
          </div>
        </div>
      )}

      {tab === 'heatmap' && (
        <div className="bg-white border border-gray-200 rounded-2xl p-4">
          <div>
            <label className="block text-xs text-gray-500 font-medium mb-1">Місяць</label>
            <input
              type="month"
              value={heatmapMonth}
              onChange={(e) => setHeatmapMonth(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="bg-white border border-gray-200 rounded-2xl p-5">
        {loading ? (
          <div className="h-64 flex items-center justify-center text-gray-400 text-sm">
            Завантаження...
          </div>
        ) : (
          <>
            {tab === 'categories' && <CategoriesTab data={spending} />}
            {tab === 'trend'      && <MonthlyTrendChart data={trend} />}
            {tab === 'heatmap'    && <SpendingHeatmap data={heatmap} />}
          </>
        )}
      </div>
    </div>
  );
}

function CategoriesTab({ data }) {
  const fmt = useCurrency();
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SpendingPieChart data={data} />
        <CategoryBarChart data={data} />
      </div>

      {data.length > 0 && (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 text-gray-500 text-xs">
              <th className="py-2 px-3 text-left font-medium">Категорія</th>
              <th className="py-2 px-3 text-right font-medium">Сума</th>
              <th className="py-2 px-3 text-right font-medium">%</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data.map((item, i) => (
              <tr key={i} className="hover:bg-gray-50">
                <td className="py-2.5 px-3 text-gray-800">
                  {item.category?.icon} {item.category?.name ?? 'Без категорії'}
                </td>
                <td className="py-2.5 px-3 text-right font-semibold text-gray-900">
                  {fmt(item.amount)}
                </td>
                <td className="py-2.5 px-3 text-right text-gray-500">
                  {item.percentage.toFixed(1)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function DateField({ label, value, onChange }) {
  return (
    <div>
      <label className="block text-xs text-gray-500 font-medium mb-1">{label}</label>
      <input
        type="date"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
      />
    </div>
  );
}
