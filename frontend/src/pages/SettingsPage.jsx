import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import client from '../api/client';
import { useAuth } from '../context/AuthContext';
import ConnectBankModal from '../components/ConnectBankModal';
import { useCurrency } from '../hooks/useCurrency';

const CURRENCY_LABELS = { 980: 'UAH', 840: 'USD', 978: 'EUR' };
const CURRENCIES = ['UAH', 'USD', 'EUR'];

const pwSchema = yup.object({
  current_password: yup.string().required("Обов'язкове поле"),
  new_password: yup.string().min(8, 'Мінімум 8 символів').required("Обов'язкове поле"),
  confirm_password: yup
    .string()
    .oneOf([yup.ref('new_password')], 'Паролі не співпадають')
    .required("Обов'язкове поле"),
});

function flattenTree(nodes) {
  const result = [];
  for (const node of nodes) {
    result.push(node);
    if (node.children?.length) result.push(...flattenTree(node.children));
  }
  return result;
}

export default function SettingsPage() {
  const { user, updateUser } = useAuth();
  const fmt = useCurrency();
  const [accounts, setAccounts] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [syncingId, setSyncingId] = useState(null);
  const [currency, setCurrency] = useState(user?.default_currency || 'UAH');
  const [currencyStatus, setCurrencyStatus] = useState('');

  useEffect(() => {
    if (user?.default_currency) setCurrency(user.default_currency);
  }, [user?.default_currency]);

  const [categories, setCategories] = useState([]);
  const [newCatName, setNewCatName] = useState('');
  const [newCatIcon, setNewCatIcon] = useState('');
  const [catSaving, setCatSaving] = useState(false);
  const [catError, setCatError] = useState('');

  const {
    register, handleSubmit, reset, setError,
    formState: { errors, isSubmitting },
  } = useForm({ resolver: yupResolver(pwSchema) });

  const fetchAccounts = () =>
    client.get('/accounts').then((r) => setAccounts(r.data)).catch(console.error);

  const fetchCategories = () =>
    client.get('/categories').then((r) => setCategories(r.data)).catch(console.error);

  useEffect(() => { fetchAccounts(); fetchCategories(); }, []);

  const handleSync = async (id) => {
    setSyncingId(id);
    try {
      await client.post(`/accounts/${id}/sync`);
    } finally {
      setSyncingId(null);
    }
  };

  const handleDisconnect = async (id) => {
    if (!window.confirm('Відключити рахунок?\nТранзакції збережуться.')) return;
    await client.delete(`/accounts/${id}`);
    setAccounts((prev) => prev.filter((a) => a.id !== id));
  };

  const handleSaveCurrency = async () => {
    setCurrencyStatus('saving');
    try {
      await updateUser({ default_currency: currency });
      setCurrencyStatus('saved');
    } catch {
      setCurrencyStatus('error');
    } finally {
      setTimeout(() => setCurrencyStatus(''), 2500);
    }
  };

  const handleChangePassword = async (data) => {
    try {
      await client.put('/auth/password', {
        current_password: data.current_password,
        new_password: data.new_password,
      });
      reset();
      alert('Пароль успішно змінено');
    } catch (err) {
      const msg = err.response?.data?.error || 'Помилка зміни пароля';
      setError('current_password', { message: msg });
    }
  };

  const handleAddCategory = async (e) => {
    e.preventDefault();
    if (!newCatName.trim()) return;
    setCatSaving(true);
    setCatError('');
    try {
      await client.post('/categories', {
        name: newCatName.trim(),
        icon: newCatIcon.trim() || null,
      });
      setNewCatName('');
      setNewCatIcon('');
      fetchCategories();
    } catch (err) {
      setCatError(err.response?.data?.error || 'Помилка створення категорії');
    } finally {
      setCatSaving(false);
    }
  };

  const handleDeleteCategory = async (id) => {
    if (!window.confirm('Видалити категорію? Транзакції перейдуть до категорії "Інше".')) return;
    try {
      await client.delete(`/categories/${id}`);
      fetchCategories();
    } catch (err) {
      alert(err.response?.data?.error || 'Помилка видалення');
    }
  };

  const currencyBtnLabel = {
    saving: 'Збереження...',
    saved: 'Збережено ✓',
    error: 'Помилка',
    '': 'Зберегти',
  }[currencyStatus];

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Налаштування</h1>

      {/* Bank accounts */}
      <Section title="Банківські рахунки">
        {accounts.length > 0 && (
          <div className="space-y-3 mb-4">
            {accounts.map((acc) => (
              <div
                key={acc.id}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-xl"
              >
                <div>
                  <p className="text-sm font-medium text-gray-900 capitalize">
                    {acc.bank_type} · {CURRENCY_LABELS[acc.currency_code] ?? acc.currency_code}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    Баланс: {fmt(acc.balance)}
                    {acc.last_sync_at && (
                      <> · Синх: {new Date(acc.last_sync_at).toLocaleDateString('uk-UA')}</>
                    )}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleSync(acc.id)}
                    disabled={syncingId === acc.id}
                    title="Синхронізувати"
                    className="text-xs px-3 py-1.5 border border-gray-300 rounded-lg hover:bg-white disabled:opacity-50 transition-colors"
                  >
                    {syncingId === acc.id ? '...' : '↻ Синх'}
                  </button>
                  <button
                    onClick={() => handleDisconnect(acc.id)}
                    className="text-xs px-3 py-1.5 border border-red-200 text-red-600 rounded-lg hover:bg-red-50 transition-colors"
                  >
                    Відключити
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {accounts.length === 0 && (
          <p className="text-sm text-gray-400 mb-4">Рахунків ще немає</p>
        )}

        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          + Підключити Monobank
        </button>
      </Section>

      {/* Default currency */}
      <Section title="Валюта за замовчуванням">
        <div className="flex items-center gap-3">
          <select
            value={currency}
            onChange={(e) => setCurrency(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
          >
            {CURRENCIES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <button
            onClick={handleSaveCurrency}
            disabled={currencyStatus === 'saving'}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 ${
              currencyStatus === 'saved'
                ? 'bg-emerald-600 text-white'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {currencyBtnLabel}
          </button>
        </div>
      </Section>

      {/* Categories */}
      <Section title="Категорії">
        {(() => {
          const flat = flattenTree(categories);
          const userCats = flat.filter((c) => c.user_id !== null);
          const systemCats = flat.filter((c) => c.user_id === null);
          return (
            <>
              {userCats.length > 0 && (
                <div className="mb-4">
                  <p className="text-xs text-gray-500 font-medium mb-2">Мої категорії</p>
                  <div className="flex flex-wrap gap-2">
                    {userCats.map((cat) => (
                      <div
                        key={cat.id}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 border border-blue-100 rounded-full text-sm text-blue-800 group"
                      >
                        {cat.icon && <span>{cat.icon}</span>}
                        <span>{cat.name}</span>
                        <button
                          onClick={() => handleDeleteCategory(cat.id)}
                          className="ml-0.5 text-blue-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity leading-none"
                          title="Видалити"
                        >
                          ✕
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="mb-4">
                <p className="text-xs text-gray-500 font-medium mb-2">Системні категорії</p>
                <div className="flex flex-wrap gap-2">
                  {systemCats.map((cat) => (
                    <span
                      key={cat.id}
                      className="px-3 py-1.5 bg-gray-50 border border-gray-200 rounded-full text-sm text-gray-600"
                    >
                      {cat.icon && <span className="mr-1">{cat.icon}</span>}
                      {cat.name}
                    </span>
                  ))}
                </div>
              </div>

              <form onSubmit={handleAddCategory} className="flex flex-wrap gap-2 items-end">
                <div>
                  <label className="block text-xs text-gray-500 font-medium mb-1">Назва</label>
                  <input
                    value={newCatName}
                    onChange={(e) => setNewCatName(e.target.value)}
                    placeholder="Назва категорії"
                    maxLength={100}
                    className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none w-48"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 font-medium mb-1">Емодзі</label>
                  <input
                    value={newCatIcon}
                    onChange={(e) => setNewCatIcon(e.target.value)}
                    placeholder="🏷️"
                    maxLength={10}
                    className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none w-20 text-center"
                  />
                </div>
                <button
                  type="submit"
                  disabled={catSaving || !newCatName.trim()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
                >
                  {catSaving ? 'Збереження...' : '+ Додати'}
                </button>
              </form>
              {catError && <p className="text-red-500 text-xs mt-2">{catError}</p>}
            </>
          );
        })()}
      </Section>

      {/* Change password */}
      <Section title="Зміна пароля">
        <form onSubmit={handleSubmit(handleChangePassword)} className="space-y-3 max-w-sm">
          <Field label="Поточний пароль" error={errors.current_password?.message}>
            <input
              {...register('current_password')}
              type="password"
              autoComplete="current-password"
              className={inputCls(!!errors.current_password)}
            />
          </Field>

          <Field label="Новий пароль" error={errors.new_password?.message}>
            <input
              {...register('new_password')}
              type="password"
              autoComplete="new-password"
              placeholder="Мінімум 8 символів"
              className={inputCls(!!errors.new_password)}
            />
          </Field>

          <Field label="Підтвердіть новий пароль" error={errors.confirm_password?.message}>
            <input
              {...register('confirm_password')}
              type="password"
              autoComplete="new-password"
              className={inputCls(!!errors.confirm_password)}
            />
          </Field>

          <button
            type="submit"
            disabled={isSubmitting}
            className="px-5 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {isSubmitting ? 'Збереження...' : 'Змінити пароль'}
          </button>
        </form>
      </Section>

      {showModal && (
        <ConnectBankModal
          onSuccess={fetchAccounts}
          onClose={() => setShowModal(false)}
        />
      )}
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-5">
      <h2 className="text-base font-semibold text-gray-800 mb-4">{title}</h2>
      {children}
    </div>
  );
}

function Field({ label, error, children }) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-700 mb-1">{label}</label>
      {children}
      {error && <p className="text-red-500 text-xs mt-1">{error}</p>}
    </div>
  );
}

const inputCls = (hasError) =>
  `w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition ${
    hasError ? 'border-red-400 bg-red-50' : 'border-gray-300'
  }`;
