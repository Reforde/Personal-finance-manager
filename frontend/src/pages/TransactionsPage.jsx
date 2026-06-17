import { useEffect, useState, useCallback } from 'react';
import { format } from 'date-fns';
import client from '../api/client';
import { formatCurrency } from '../utils/formatCurrency';
import TransactionList from '../components/TransactionList';
import TransactionForm from '../components/TransactionForm';
import CategorySelect from '../components/CategorySelect';

const TYPES = [
  { value: 'all',     label: 'Всі' },
  { value: 'expense', label: 'Витрати' },
  { value: 'income',  label: 'Доходи' },
];

const DEFAULT_FILTERS = {
  from: format(new Date(new Date().getFullYear(), new Date().getMonth(), 1), 'yyyy-MM-dd'),
  to: format(new Date(), 'yyyy-MM-dd'),
  type: 'all',
  category_id: null,
  page: 1,
};

export default function TransactionsPage() {
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [data, setData] = useState({ items: [], total: 0, pages: 1 });
  const [categories, setCategories] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    client.get('/categories').then((r) => setCategories(r.data)).catch(console.error);
  }, []);

  const fetchTransactions = useCallback(() => {
    setLoading(true);
    const params = new URLSearchParams({ page: filters.page, per_page: 20 });
    if (filters.from) params.set('from', filters.from + 'T00:00:00');
    if (filters.to)   params.set('to',   filters.to   + 'T23:59:59');
    if (filters.type !== 'all') params.set('type', filters.type);
    if (filters.category_id)    params.set('category_id', filters.category_id);

    client.get(`/transactions?${params}`)
      .then((r) => setData(r.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [filters]);

  useEffect(() => { fetchTransactions(); }, [fetchTransactions]);

  const setFilter = (key, value) =>
    setFilters((f) => ({ ...f, [key]: value, page: key !== 'page' ? 1 : value }));

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Транзакції</h1>
        <button
          onClick={() => setShowForm(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          + Додати
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white border border-gray-200 rounded-2xl p-4 flex flex-wrap gap-3 items-end">
        <FilterField label="Від">
          <input
            type="date"
            value={filters.from}
            onChange={(e) => setFilter('from', e.target.value)}
            className={inputCls}
          />
        </FilterField>

        <FilterField label="До">
          <input
            type="date"
            value={filters.to}
            onChange={(e) => setFilter('to', e.target.value)}
            className={inputCls}
          />
        </FilterField>

        <FilterField label="Тип">
          <select
            value={filters.type}
            onChange={(e) => setFilter('type', e.target.value)}
            className={inputCls}
          >
            {TYPES.map(({ value, label }) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </FilterField>

        <FilterField label="Категорія">
          <CategorySelect
            categories={categories}
            value={filters.category_id}
            onChange={(v) => setFilter('category_id', v)}
            placeholder="Всі категорії"
            className="min-w-40"
          />
        </FilterField>

        <button
          onClick={() => setFilters(DEFAULT_FILTERS)}
          className="text-xs text-gray-400 hover:text-gray-600 self-end pb-2"
        >
          Скинути
        </button>
      </div>

      {/* Summary row */}
      <p className="text-sm text-gray-500">
        Знайдено: <strong>{data.total}</strong> транзакцій
      </p>

      {/* List */}
      <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-sm text-gray-400">Завантаження...</div>
        ) : (
          <TransactionList
            transactions={data.items}
            categories={categories}
            onRefresh={fetchTransactions}
          />
        )}
      </div>

      {/* Pagination */}
      {data.pages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            disabled={filters.page <= 1}
            onClick={() => setFilter('page', filters.page - 1)}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50"
          >
            ← Назад
          </button>
          <span className="text-sm text-gray-500">
            {filters.page} / {data.pages}
          </span>
          <button
            disabled={filters.page >= data.pages}
            onClick={() => setFilter('page', filters.page + 1)}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50"
          >
            Далі →
          </button>
        </div>
      )}

      {/* Modal */}
      {showForm && (
        <TransactionForm
          categories={categories}
          onSuccess={fetchTransactions}
          onClose={() => setShowForm(false)}
        />
      )}
    </div>
  );
}

function FilterField({ label, children }) {
  return (
    <div>
      <label className="block text-xs text-gray-500 font-medium mb-1">{label}</label>
      {children}
    </div>
  );
}

const inputCls = 'border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500';
