import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { format } from 'date-fns';
import client from '../api/client';
import CategorySelect from './CategorySelect';

const schema = yup.object({
  amount: yup
    .number()
    .typeError('Введіть число')
    .positive('Сума має бути більше 0')
    .required("Обов'язкове поле"),
  description: yup.string().max(500).default(''),
  category_id: yup.number().nullable().default(null),
  timestamp: yup.string().required("Обов'язкове поле"),
  type: yup.string().oneOf(['income', 'expense']).required(),
});

export default function TransactionForm({ categories = [], onSuccess, onClose }) {
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: yupResolver(schema),
    defaultValues: {
      type: 'expense',
      timestamp: format(new Date(), "yyyy-MM-dd'T'HH:mm"),
      description: '',
      category_id: null,
    },
  });

  const txType = watch('type');

  const onSubmit = async (data) => {
    await client.post('/transactions', {
      amount: Math.round(data.amount * 100),
      description: data.description || '',
      category_id: data.category_id || null,
      timestamp: data.timestamp,
      type: data.type,
    });
    onSuccess();
    onClose();
  };

  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-bold text-gray-900">Нова операція</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl leading-none"
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Type toggle */}
          <div className="flex rounded-lg border border-gray-200 overflow-hidden">
            {[
              { value: 'expense', label: 'Витрата', active: 'bg-red-500 text-white' },
              { value: 'income',  label: 'Дохід',   active: 'bg-emerald-500 text-white' },
            ].map(({ value, label, active }) => (
              <label key={value} className="flex-1 cursor-pointer">
                <input {...register('type')} type="radio" value={value} className="sr-only" />
                <div
                  className={`py-2 text-center text-sm font-medium transition-colors ${
                    txType === value ? active : 'text-gray-500 hover:bg-gray-50'
                  }`}
                >
                  {label}
                </div>
              </label>
            ))}
          </div>

          <Field label="Сума (₴)" error={errors.amount?.message}>
            <input
              {...register('amount')}
              type="number"
              step="0.01"
              min="0.01"
              placeholder="0.00"
              className={inputCls(!!errors.amount)}
            />
          </Field>

          <Field label="Дата і час" error={errors.timestamp?.message}>
            <input
              {...register('timestamp')}
              type="datetime-local"
              className={inputCls(!!errors.timestamp)}
            />
          </Field>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Категорія</label>
            <CategorySelect
              categories={categories}
              value={watch('category_id')}
              onChange={(v) => setValue('category_id', v)}
              placeholder="Без категорії"
              className="w-full"
            />
          </div>

          <Field label="Опис" error={errors.description?.message}>
            <input
              {...register('description')}
              type="text"
              placeholder="Необовʼязково"
              className={inputCls(!!errors.description)}
            />
          </Field>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Скасувати
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {isSubmitting ? 'Збереження...' : 'Додати'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function Field({ label, error, children }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      {children}
      {error && <p className="text-red-500 text-xs mt-1">{error}</p>}
    </div>
  );
}

const inputCls = (hasError) =>
  `w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition ${
    hasError ? 'border-red-400 bg-red-50' : 'border-gray-300'
  }`;
