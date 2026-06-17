import { useEffect, useRef, useState } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { uk } from 'date-fns/locale';
import client from '../api/client';

const TYPE_CONFIG = {
  budget_warning: {
    icon: '⚠️',
    label: 'Попередження',
    bg: 'bg-yellow-50',
    border: 'border-yellow-200',
    badge: 'bg-yellow-100 text-yellow-800',
    dot: 'bg-yellow-400',
  },
  budget_exceeded: {
    icon: '🚨',
    label: 'Перевищено',
    bg: 'bg-red-50',
    border: 'border-red-200',
    badge: 'bg-red-100 text-red-700',
    dot: 'bg-red-500',
  },
  large_transaction: {
    icon: '💸',
    label: 'Велика транзакція',
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    badge: 'bg-blue-100 text-blue-700',
    dot: 'bg-blue-400',
  },
};

const DEFAULT_CONFIG = {
  icon: '🔔',
  label: 'Сповіщення',
  bg: 'bg-gray-50',
  border: 'border-gray-200',
  badge: 'bg-gray-100 text-gray-700',
  dot: 'bg-gray-400',
};

export default function NotificationBell() {
  const [notifications, setNotifications] = useState([]);
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  const unread = notifications.filter((n) => !n.is_read).length;

  const fetch = () =>
    client.get('/notifications').then((r) => setNotifications(r.data)).catch(() => {});

  useEffect(() => {
    fetch();
    const id = setInterval(fetch, 60_000);
    return () => clearInterval(id);
  }, []);

  // Close on outside click
  useEffect(() => {
    function handler(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  function toggle() {
    setOpen((v) => !v);
  }

  function markRead(id) {
    client.put(`/notifications/${id}/read`).then(() =>
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      )
    );
  }

  function markAllRead() {
    client.put('/notifications/read-all').then(() =>
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })))
    );
  }

  return (
    <div className="relative" ref={ref}>
      {/* Bell button */}
      <button
        onClick={toggle}
        className="relative p-2 rounded-lg text-gray-500 hover:bg-gray-100 hover:text-gray-700 transition-colors"
        aria-label="Сповіщення"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="w-5 h-5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1.8}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6 6 0 10-12 0v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
          />
        </svg>
        {unread > 0 && (
          <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] flex items-center justify-center rounded-full bg-red-500 text-white text-[10px] font-bold px-1 leading-none">
            {unread > 9 ? '9+' : unread}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {open && (
        <div className="absolute left-0 top-10 z-50 w-80 bg-white rounded-2xl shadow-xl border border-gray-200 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
            <span className="text-sm font-semibold text-gray-800">Сповіщення</span>
            {unread > 0 && (
              <button
                onClick={markAllRead}
                className="text-xs text-blue-600 hover:text-blue-800 font-medium transition-colors"
              >
                Позначити всі прочитаними
              </button>
            )}
          </div>

          {/* List */}
          <div className="max-h-[400px] overflow-y-auto divide-y divide-gray-50">
            {notifications.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-10 text-gray-400">
                <span className="text-3xl mb-2">🔔</span>
                <p className="text-sm">Немає сповіщень</p>
              </div>
            ) : (
              notifications.map((n) => {
                const cfg = TYPE_CONFIG[n.type] ?? DEFAULT_CONFIG;
                return (
                  <button
                    key={n.id}
                    onClick={() => !n.is_read && markRead(n.id)}
                    className={`w-full text-left px-4 py-3 flex gap-3 items-start transition-colors ${
                      n.is_read ? 'bg-white hover:bg-gray-50' : cfg.bg + ' hover:brightness-95'
                    }`}
                  >
                    {/* Unread dot */}
                    <span className="mt-1.5 shrink-0">
                      {!n.is_read ? (
                        <span className={`block w-2 h-2 rounded-full ${cfg.dot}`} />
                      ) : (
                        <span className="block w-2 h-2" />
                      )}
                    </span>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5 mb-0.5">
                        <span>{cfg.icon}</span>
                        <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full ${cfg.badge}`}>
                          {cfg.label}
                        </span>
                      </div>
                      <p className={`text-sm leading-snug ${n.is_read ? 'text-gray-500' : 'text-gray-800 font-medium'}`}>
                        {n.message}
                      </p>
                      <p className="text-[11px] text-gray-400 mt-1">
                        {formatDistanceToNow(new Date(n.created_at), {
                          addSuffix: true,
                          locale: uk,
                        })}
                      </p>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
