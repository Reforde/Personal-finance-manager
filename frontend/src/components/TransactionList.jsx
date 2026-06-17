import { useState, useEffect } from 'react';
import { format } from 'date-fns';
import { uk } from 'date-fns/locale';
import client from '../api/client';
import { useCurrency } from '../hooks/useCurrency';
import CategorySelect from './CategorySelect';

export default function TransactionList({ transactions = [], categories = [], onRefresh }) {
  const fmt = useCurrency();
  const [editingId, setEditingId] = useState(null);
  const [hiddenIds, setHiddenIds] = useState(new Set());

  // Reset hidden IDs when the transactions list is refreshed from parent
  useEffect(() => { setHiddenIds(new Set()); }, [transactions]);

  const handleCategoryChange = async (txId, categoryId) => {
    try {
      await client.put(`/transactions/${txId}`, { category_id: categoryId });
      onRefresh();
    } catch (e) {
      console.error(e);
    } finally {
      setEditingId(null);
    }
  };

  const handleDelete = async (txId) => {
    if (!window.confirm('Видалити транзакцію?')) return;
    // Optimistic: hide immediately before server responds
    setHiddenIds((prev) => new Set([...prev, txId]));
    try {
      await client.delete(`/transactions/${txId}`);
      onRefresh();
    } catch (e) {
      // Rollback if request failed
      setHiddenIds((prev) => { const s = new Set(prev); s.delete(txId); return s; });
      console.error(e);
    }
  };

  const visible = transactions.filter((tx) => !hiddenIds.has(tx.id));

  if (!visible.length) {
    return (
      <div className="text-center py-12 text-gray-400 text-sm">
        Транзакцій не знайдено
      </div>
    );
  }

  return (
    <>
      {/* Desktop table */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 text-gray-500 text-xs">
              <th className="py-3 px-4 text-left font-medium">Дата</th>
              <th className="py-3 px-4 text-left font-medium">Опис</th>
              <th className="py-3 px-4 text-left font-medium">Категорія</th>
              <th className="py-3 px-4 text-right font-medium">Сума</th>
              <th className="py-3 px-4" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {visible.map((tx) => (
              <tr key={tx.id} className="hover:bg-gray-50 transition-colors">
                <td className="py-3 px-4 text-gray-500 whitespace-nowrap">
                  {format(new Date(tx.timestamp), 'dd MMM yyyy', { locale: uk })}
                </td>
                <td className="py-3 px-4 text-gray-800 max-w-xs truncate">
                  {tx.description || <span className="text-gray-400 italic">без опису</span>}
                </td>
                <td className="py-3 px-4">
                  {editingId === tx.id ? (
                    <CategorySelect
                      categories={categories}
                      value={tx.category_id}
                      onChange={(v) => handleCategoryChange(tx.id, v)}
                      placeholder="Без категорії"
                      className="w-44"
                    />
                  ) : (
                    <button
                      onClick={() => setEditingId(tx.id)}
                      className="text-left text-gray-600 hover:text-blue-600 hover:underline transition-colors"
                    >
                      {tx.category
                        ? [tx.category.icon, tx.category.name].filter(Boolean).join(' ')
                        : <span className="text-gray-400 italic">—</span>}
                    </button>
                  )}
                </td>
                <td className={`py-3 px-4 text-right font-semibold whitespace-nowrap ${
                  tx.transaction_type === 'income' ? 'text-emerald-600' : 'text-red-500'
                }`}>
                  {tx.transaction_type === 'income' ? '+' : ''}
                  {fmt(tx.amount)}
                </td>
                <td className="py-3 px-4 text-right">
                  {tx.is_manual && (
                    <button
                      onClick={() => handleDelete(tx.id)}
                      className="text-gray-300 hover:text-red-500 transition-colors text-xs"
                      title="Видалити"
                    >
                      ✕
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile cards */}
      <div className="md:hidden space-y-2">
        {visible.map((tx) => (
          <div key={tx.id} className="bg-white border border-gray-200 rounded-xl p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {tx.description || <span className="text-gray-400 italic">без опису</span>}
                </p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {format(new Date(tx.timestamp), 'dd MMM yyyy', { locale: uk })}
                  {tx.category && ` · ${[tx.category.icon, tx.category.name].filter(Boolean).join(' ')}`}
                </p>
              </div>
              <span className={`text-sm font-bold shrink-0 ${
                tx.transaction_type === 'income' ? 'text-emerald-600' : 'text-red-500'
              }`}>
                {tx.transaction_type === 'income' ? '+' : ''}
                {fmt(tx.amount)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
