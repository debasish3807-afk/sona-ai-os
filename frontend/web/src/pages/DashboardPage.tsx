import { useQuery } from '@tanstack/react-query';
import { apiRequest } from '../api/client';

function StatCard({ label, value, icon }: { label: string; value: string | number; icon: string }) {
  return (
    <div className="p-6 rounded-2xl bg-white/5 backdrop-blur border border-white/10 hover:border-white/20 transition-all">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-400 text-sm">{label}</p>
          <p className="text-2xl font-bold text-white mt-1">{value}</p>
        </div>
        <span className="text-3xl">{icon}</span>
      </div>
    </div>
  );
}

export function DashboardPage() {
  const { data: health } = useQuery({ queryKey: ['health'], queryFn: () => apiRequest<any>('/health') });
  const { data: providers } = useQuery({ queryKey: ['providers'], queryFn: () => apiRequest<any>('/health/providers').catch(() => ({ providers: [] })) });
  const { data: tools } = useQuery({ queryKey: ['tools-status'], queryFn: () => apiRequest<any>('/tools/status').catch(() => ({})) });
  const { data: mcp } = useQuery({ queryKey: ['mcp'], queryFn: () => apiRequest<any>('/mcp').catch(() => ({})) });

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
        Dashboard
      </h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard label="AI Status" value={health?.status === 'healthy' ? 'Online' : 'Offline'} icon="🧠" />
        <StatCard label="Providers" value={providers?.providers?.length || 0} icon="🔌" />
        <StatCard label="Tools" value={tools?.tools_registered || 0} icon="🔧" />
        <StatCard label="MCP Status" value={mcp?.status || 'unknown'} icon="⚡" />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="p-6 rounded-2xl bg-white/5 backdrop-blur border border-white/10">
          <h3 className="text-lg font-semibold mb-4">Provider Health</h3>
          {providers?.providers?.map((p: any) => (
            <div key={p.provider_id} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
              <span className="text-gray-300">{p.name}</span>
              <span className={`text-sm font-medium ${p.healthy ? 'text-green-400' : 'text-red-400'}`}>
                {p.healthy ? '● Healthy' : '○ Unavailable'}
              </span>
            </div>
          )) || <p className="text-gray-500">No providers connected</p>}
        </div>
        <div className="p-6 rounded-2xl bg-white/5 backdrop-blur border border-white/10">
          <h3 className="text-lg font-semibold mb-4">System Info</h3>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between"><span className="text-gray-400">Version</span><span>{health?.version || '0.8.0'}</span></div>
            <div className="flex justify-between"><span className="text-gray-400">Sessions</span><span>{tools?.active_sessions || 0}</span></div>
            <div className="flex justify-between"><span className="text-gray-400">Executions</span><span>{tools?.total_executions || 0}</span></div>
            <div className="flex justify-between"><span className="text-gray-400">Safe Mode</span><span>{tools?.safe_mode ? 'On' : 'Off'}</span></div>
          </div>
        </div>
      </div>
    </div>
  );
}
