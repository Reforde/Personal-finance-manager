import { useEffect, useState, useCallback } from 'react';
import { format, subMonths, parseISO } from 'date-fns';
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import client from '../api/client';
import BudgetCard from '../components/BudgetCard';
import CategorySelect from '../components/CategorySelect';

const schema = yup.object({
  category_id: yup.number().required('Оберіть категорію').typeError('Оберіть категорію'),
  amount: yup
    .number()
    .typeError('Введіть число')
    .positive('Сума має бути більше 0')
    .required("Обов'язкове поле"),
});

export default function BudgetsPage() {
  const [selectedMonth, setSelectedMonth] = useState(format(new Date(), 'yyyy-MM'));
  const [budgets, setBudgets] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [copyStatus, setCopyStatus] = useState('');

  const { register, handleSubmit, reset, watch, setValue, formState: { errors, isSubmitting } } =
    useForm({ resolver: yupResolver(schema) });

  useEffect(() => {
    client.get('/categories').then((r) => setCategories(r.data)).catch(console.error);
  }, []);

  const fetchBudgets = useCallback(() => {
    setLoading(true);
    client.get(`/budgets?month=${selectedMonth}`)
      .then((r) => setBudgets(r.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [selectedMonth]);

  useEffect(() => { fetchBudgets(); }, [fetchBudgets]);

  const onAddBudget = async (data) => {
    try {
      await client.post('/budgets', {
        category_id: data.category_id,
        month: selectedMonth,
        planned_amount: Math.round(data.amount * 100),
      });
      reset();
      fetchBudgets();
    } catch (err) {
      const msg = err.response?.data?.error || 'Помилка створення бюджету';
      alert(msg);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Видалити бюджет?')) return;
    await client.delete(`/budgets/${id}`);
    fetchBudgets();
  };

  const handleCopyPrev = async () => {
    const prevMonth = format(subMonths(parseISO(selectedMonth + '-01'), 1), 'yyyy-MM');
    setCopyStatus('copying');
    try {
      const res = await client.post('/budgets/copy', {
        from_month: prevMonth,
        to_month: selectedMonth,
      });
      if (res.data.length === 0) {
        setCopyStatus('empty');
      } else {
        setCopyStatus('done');
        fetchBudgets();
      }
    } catch (err) {
      setCopyStatus('error');
    } finally {
      setTimeout(() => setCopyStatus(''), 3000);
    }
  };

  const copyLabel = {
    copying: 'Копіювання...',
    done: 'Скопійовано!',
    empty: 'Нема що копіювати',
    error: 'Помилка',
    '': 'Копіювати з попереднього місяця',
  }[copyStatus];

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-gray-900">Бюджети</h1>

        <div className="flex items-center gap-3">
          <input
            type="month"
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
          />
          <button
            onClick={handleCopyPrev}
            disabled={copyStatus === 'copying'}
            className="text-sm px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors"
          >
            {copyLabel}
          </button>
        </div>
      </div>

      {/* Budget list */}
      {loading ? (
        <div className="text-sm text-gray-400 text-center py-10">Завантаження...</div>
      ) : budgets.length === 0 ? (
        <div className="text-sm text-gray-400 text-center py-10 bg-white border border-gray-200 rounded-2xl">
          Бюджетів на {selectedMonth} ще немає
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {budgets.map((b) => (
            <div key={b.id} className="relative group">
              <BudgetCard budget={b} />
              <button
                onClick={() => handleDelete(b.id)}
                className="absolute top-3 right-3 text-gray-300 hover:text-red-500 text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                title="Видалити"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Add budget form */}
      <div className="bg-white border border-gray-200 rounded-2xl p-5">
        <h2 className="text-base font-semibold text-gray-800 mb-4">Додати бюджет</h2>

        <form onSubmit={handleSubmit(onAddBudget)} className="flex flex-wrap gap-3 items-end">
          <div>
            <label className="block text-xs text-gray-500 font-medium mb-1">Категорія</label>
            <CategorySelect
              categories={categories}
              value={watch('category_id')}
              onChange={(v) => setValue('category_id', v, { shouldValidate: true })}
              placeholder="Оберіть категорію"
              className="min-w-48"
            />
            {errors.category_id && (
              <p className="text-red-500 text-xs mt-1">{errors.category_id.message}</p>
            )}
          </div>

          <div>
            <label className="block text-xs text-gray-500 font-medium mb-1">Ліміт (₴)</label>
            <input
              {...register('amount')}
              type="number"
              step="0.01"
              min="0.01"
              placeholder="0.00"
              className={`border rounded-lg px-3 py-2 text-sm w-36 focus:ring-2 focus:ring-blue-500 focus:outline-none ${
                errors.amount ? 'border-red-400' : 'border-gray-300'
              }`}
            />
            {errors.amount && (
              <p className="text-red-500 text-xs mt-1">{errors.amount.message}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="px-5 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {isSubmitting ? 'Збереження...' : 'Додати'}
          </button>
        </form>
      </div>
    </div>
  );
}
