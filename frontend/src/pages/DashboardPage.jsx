import { useEffect, useState, useRef, useCallback } from 'react';
import { format, parseISO, endOfMonth, subMonths, addMonths } from 'date-fns';
import { uk } from 'date-fns/locale';
import { Link } from 'react-router-dom';
import client from '../api/client';
import { useAuth } from '../context/AuthContext';
import { useRates } from '../context/RatesContext';
import { useCurrency } from '../hooks/useCurrency';
import SpendingPieChart from '../components/charts/SpendingPieChart';
import BudgetCard from '../components/BudgetCard';
import TransactionList from '../components/TransactionList';

function monthDateRange(selectedMonth) {
  const now = new Date();
  const currentMonth = format(now, 'yyyy-MM');
  const start = `${selectedMonth}-01`;
  const end = selectedMonth === currentMonth
    ? format(now, 'yyyy-MM-dd')
    : format(endOfMonth(parseISO(start)), 'yyyy-MM-dd');
  return { start, end };
}

export default function DashboardPage() {
  const { user } = useAuth();
  const fmt = useCurrency();

  const [selectedMonth, setSelectedMonth] = useState(format(new Date(), 'yyyy-MM'));
  const [summary, setSummary] = useState(null);
  const [spending, setSpending] = useState([]);
  const [budgets, setBudgets] = useState([]);
  const [recentTx, setRecentTx] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const { start, end } = monthDateRange(selectedMonth);

    Promise.all([
      client.get(`/analytics/summary?from=${start}T00:00:00&to=${end}T23:59:59`),
      client.get(`/analytics/spending-by-category?from=${start}T00:00:00&to=${end}T23:59:59`),
      client.get(`/budgets?month=${selectedMonth}`),
      client.get(`/transactions?page=1&per_page=5&from=${start}T00:00:00&to=${end}T23:59:59`),
      client.get('/categories'),
    ])
      .then(([sum, sp, budg, tx, cats]) => {
        setSummary(sum.data);
        setSpending(sp.data);
        setBudgets(budg.data);
        setRecentTx(tx.data.items);
        setCategories(cats.data);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [selectedMonth]);

  const fetchRecentTx = useCallback(() => {
    const { start, end } = monthDateRange(selectedMonth);
    client.get(`/transactions?page=1&per_page=5&from=${start}T00:00:00&to=${end}T23:59:59`)
      .then((r) => setRecentTx(r.data.items))
      .catch(console.error);
  }, [selectedMonth]);

  const handlePrevMonth = () =>
    setSelectedMonth(format(subMonths(parseISO(`${selectedMonth}-01`), 1), 'yyyy-MM'));

  const handleNextMonth = () =>
    setSelectedMonth(format(addMonths(parseISO(`${selectedMonth}-01`), 1), 'yyyy-MM'));

  const monthLabel = format(parseISO(`${selectedMonth}-01`), 'LLLL yyyy', { locale: uk });

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-gray-900 capitalize">
          {monthLabel} — огляд
        </h1>
        <div className="flex items-center gap-1">
          <button
            onClick={handlePrevMonth}
            className="px-2 py-1.5 border border-gray-300 rounded-lg text-gray-600 hover:bg-gray-50 transition-colors text-sm"
          >
            ‹
          </button>
          <input
            type="month"
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
          />
          <button
            onClick={handleNextMonth}
            className="px-2 py-1.5 border border-gray-300 rounded-lg text-gray-600 hover:bg-gray-50 transition-colors text-sm"
          >
            ›
          </button>
        </div>
      </div>

      {loading ? <PageLoader /> : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <BalanceCard selectedMonth={selectedMonth} />
            <StatCard label="Доходи"  value={summary?.total_income  ?? 0} color="text-emerald-600" prefix="+" fmt={fmt} />
            <StatCard label="Витрати" value={summary?.total_expense ?? 0} color="text-red-500"     prefix="−" fmt={fmt} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <section className="bg-white border border-gray-200 rounded-2xl p-5">
              <h2 className="text-base font-semibold text-gray-800 mb-4">Витрати за категоріями</h2>
              <SpendingPieChart data={spending} />
            </section>

            <section className="bg-white border border-gray-200 rounded-2xl p-5">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-base font-semibold text-gray-800">Бюджети</h2>
                <Link to="/budgets" className="text-xs text-blue-600 hover:underline">Всі →</Link>
              </div>
              {budgets.length === 0 ? (
                <p className="text-sm text-gray-400 text-center py-6">Бюджетів на цей місяць немає</p>
              ) : (
                <div className="space-y-3">
                  {budgets.slice(0, 4).map((b) => <BudgetCard key={b.id} budget={b} />)}
                </div>
              )}
            </section>
          </div>

          <section className="bg-white border border-gray-200 rounded-2xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-gray-800">Транзакції місяця</h2>
              <Link
                to={`/transactions?from=${monthDateRange(selectedMonth).start}&to=${monthDateRange(selectedMonth).end}`}
                className="text-xs text-blue-600 hover:underline"
              >
                Всі →
              </Link>
            </div>
            <TransactionList transactions={recentTx} categories={categories} onRefresh={fetchRecentTx} />
          </section>
        </>
      )}
    </div>
  );
}

function BalanceCard({ selectedMonth }) {
  const { user } = useAuth();
  const { rates } = useRates();
  const fmt = useCurrency();
  const currency = user?.default_currency || 'UAH';

  const [balanceKopecks, setBalanceKopecks] = useState(0);
  const [editing, setEditing] = useState(false);
  const [inputVal, setInputVal] = useState('');
  const inputRef = useRef(null);

  useEffect(() => {
    client.get(`/balance/${selectedMonth}`)
      .then((r) => setBalanceKopecks(r.data.amount))
      .catch(console.error);
  }, [selectedMonth]);

  // Stored value is always UAH kopecks → convert to display currency units
  const toDisplayUnits = (kopecks) => {
    if (currency !== 'UAH' && rates[currency]) {
      return (kopecks / rates[currency] / 100);
    }
    return kopecks / 100;
  };

  // User enters value in display currency → convert back to UAH kopecks
  const toUahKopecks = (displayUnits) => {
    if (currency !== 'UAH' && rates[currency]) {
      return Math.round(displayUnits * rates[currency] * 100);
    }
    return Math.round(displayUnits * 100);
  };

  const handleEdit = () => {
    const displayVal = balanceKopecks ? toDisplayUnits(balanceKopecks).toFixed(2) : '';
    setInputVal(displayVal);
    setEditing(true);
    setTimeout(() => inputRef.current?.focus(), 0);
  };

  const handleSave = () => {
    const kopecks = toUahKopecks(parseFloat(inputVal || '0'));
    client.put(`/balance/${selectedMonth}`, { amount: kopecks })
      .then((r) => setBalanceKopecks(r.data.amount))
      .catch(console.error);
    setEditing(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleSave();
    if (e.key === 'Escape') setEditing(false);
  };

  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-5">
      <p className="text-xs text-gray-500 font-medium uppercase tracking-wide mb-1">Баланс</p>
      {editing ? (
        <div className="flex items-center gap-2 mt-1">
          <input
            ref={inputRef}
            type="number"
            step="0.01"
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            onBlur={handleSave}
            onKeyDown={handleKeyDown}
            placeholder="0.00"
            className="w-full border border-blue-400 rounded-lg px-2 py-1 text-lg font-bold text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <span className="text-gray-400 text-sm shrink-0">{currency}</span>
        </div>
      ) : (
        <button
          onClick={handleEdit}
          className="w-full text-left group"
          title="Натисніть щоб змінити"
        >
          {balanceKopecks ? (
            <p className="text-2xl font-bold text-gray-900 group-hover:text-blue-600 transition-colors">
              {fmt(balanceKopecks)}
            </p>
          ) : (
            <p className="text-sm text-gray-400 mt-1 group-hover:text-blue-500 transition-colors">
              Введіть свій баланс
            </p>
          )}
        </button>
      )}
    </div>
  );
}

function StatCard({ label, value, color, prefix = '', fmt }) {
  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-5">
      <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">{label}</p>
      <p className={`text-2xl font-bold mt-1 ${color}`}>
        {prefix}{fmt(Math.abs(value))}
      </p>
    </div>
  );
}

function PageLoader() {
  return (
    <div className="p-6 space-y-4 animate-pulse">
      <div className="grid grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => <div key={i} className="h-24 bg-gray-200 rounded-2xl" />)}
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="h-64 bg-gray-200 rounded-2xl" />
        <div className="h-64 bg-gray-200 rounded-2xl" />
      </div>
    </div>
  );
}
