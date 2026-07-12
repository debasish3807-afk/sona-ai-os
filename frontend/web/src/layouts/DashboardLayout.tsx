import { Link, Outlet, useLocation } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

const navItems = [
  { path: '/', label: 'Dashboard', icon: '◉' },
  { path: '/chat', label: 'AI Chat', icon: '💬' },
  { path: '/memory', label: 'Memory', icon: '🧠' },
  { path: '/documents', label: 'Documents', icon: '📄' },
  { path: '/tools', label: 'Tools', icon: '🔧' },
  { path: '/settings', label: 'Settings', icon: '⚙' },
];

export function DashboardLayout() {
  const location = useLocation();
  const { user, logout } = useAuthStore();

  return (
    <div className="flex h-screen bg-gray-900 text-white">
      {/* Sidebar */}
      <nav className="w-64 bg-gray-900/50 backdrop-blur-xl border-r border-white/5 flex flex-col">
        <div className="p-6 border-b border-white/5">
          <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            Sona AI OS
          </h1>
        </div>
        <div className="flex-1 py-4 space-y-1 px-3">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                location.pathname === item.path
                  ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <span>{item.icon}</span>
              <span className="text-sm font-medium">{item.label}</span>
            </Link>
          ))}
        </div>
        <div className="p-4 border-t border-white/5">
          <div className="flex items-center gap-3 px-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-xs font-bold">
              {user?.username?.[0]?.toUpperCase() || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{user?.username}</p>
              <p className="text-xs text-gray-500">{user?.role}</p>
            </div>
            <button onClick={logout} className="text-gray-500 hover:text-red-400 text-sm" title="Logout">✕</button>
          </div>
        </div>
      </nav>
      {/* Main Content */}
      <main className="flex-1 overflow-auto bg-gray-950">
        <Outlet />
      </main>
    </div>
  );
}
