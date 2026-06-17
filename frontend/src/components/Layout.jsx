import { NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import NotificationBell from './NotificationBell';

const NAV = [
  { to: '/dashboard',    label: 'Головна',        icon: '📊' },
  { to: '/transactions', label: 'Транзакції',     icon: '💳' },
  { to: '/budgets',      label: 'Бюджети',        icon: '🎯' },
  { to: '/analytics',   label: 'Аналітика',      icon: '📈' },
  { to: '/settings',    label: 'Налаштування',   icon: '⚙️' },
];

export default function Layout() {
  const { user, logout } = useAuth();

  return (
    <div className="flex min-h-screen bg-gray-50">
      <aside className="w-60 shrink-0 bg-white border-r border-gray-200 flex flex-col">
        <div className="px-6 py-5 border-b border-gray-200 flex items-center justify-between gap-2">
          <div className="min-w-0">
            <p className="text-lg font-bold text-gray-900">Фінанси</p>
            <p className="text-xs text-gray-400 mt-0.5 truncate">{user?.email}</p>
          </div>
          <NotificationBell />
        </div>

        <nav className="flex-1 p-3 space-y-0.5">
          {NAV.map(({ to, label, icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`
              }
            >
              <span>{icon}</span>
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="p-3 border-t border-gray-200">
          <button
            onClick={logout}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-100 transition-colors"
          >
            <span>🚪</span> Вийти
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
