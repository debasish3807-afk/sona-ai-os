import { useThemeStore } from '../stores/themeStore';
import { useAuthStore } from '../stores/authStore';

export function SettingsPage() {
  const { theme, setTheme } = useThemeStore();
  const user = useAuthStore((s) => s.user);

  return (
    <div className="p-8 max-w-2xl">
      <h1 className="text-3xl font-bold mb-8 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">Settings</h1>
      <section className="mb-8 p-6 rounded-2xl bg-white/5 border border-white/10">
        <h3 className="text-lg font-semibold mb-4">Profile</h3>
        <div className="space-y-2 text-sm">
          <p><span className="text-gray-400">Username:</span> <span className="text-white">{user?.username}</span></p>
          <p><span className="text-gray-400">Email:</span> <span className="text-white">{user?.email}</span></p>
          <p><span className="text-gray-400">Role:</span> <span className="text-blue-400">{user?.role}</span></p>
        </div>
      </section>
      <section className="p-6 rounded-2xl bg-white/5 border border-white/10">
        <h3 className="text-lg font-semibold mb-4">Theme</h3>
        <div className="flex gap-3">
          {(['dark', 'light', 'system'] as const).map((t) => (
            <button key={t} onClick={() => setTheme(t)}
              className={`px-4 py-2 rounded-lg text-sm capitalize ${theme === t ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30' : 'bg-white/5 text-gray-400 hover:text-white'}`}>
              {t}
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}
