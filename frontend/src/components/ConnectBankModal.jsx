import { useEffect, useState } from 'react';
import client from '../api/client';

export default function ConnectBankModal({ onSuccess, onClose }) {
  const [token, setToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  const handleConnect = async () => {
    const trimmed = token.trim();
    if (!trimmed) return;

    setLoading(true);
    setError('');
    try {
      await client.post('/accounts/connect', { bank_type: 'monobank', token: trimmed });
      onSuccess();
      onClose();
    } catch (err) {
      setError(err.response?.data?.error || 'Помилка підключення. Перевірте токен.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-gray-900">Підключити Monobank</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">✕</button>
        </div>

        <p className="text-sm text-gray-500 mb-1">Як отримати токен:</p>
        <ol className="text-sm text-gray-500 list-decimal ml-5 mb-4 space-y-0.5">
          <li>Відкрийте додаток Monobank</li>
          <li>Налаштування → Інше → API</li>
          <li>Скопіюйте токен</li>
        </ol>

        <input
          type="text"
          value={token}
          onChange={(e) => { setToken(e.target.value); setError(''); }}
          placeholder="u…  (токен Monobank)"
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-3 focus:ring-2 focus:ring-blue-500 focus:outline-none font-mono"
          autoFocus
        />

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg mb-3">
            {error}
          </div>
        )}

        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Скасувати
          </button>
          <button
            onClick={handleConnect}
            disabled={!token.trim() || loading}
            className="flex-1 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Підключення...' : 'Підключити'}
          </button>
        </div>
      </div>
    </div>
  );
}
