import { useQuery } from '@tanstack/react-query';
import { apiRequest } from '../api/client';

export function ToolsPage() {
  const { data } = useQuery({ queryKey: ['tools'], queryFn: () => apiRequest<any>('/tools') });
  const tools = data?.tools || [];

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">Tools ({tools.length})</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {tools.map((tool: any) => (
          <div key={tool.name} className="p-4 rounded-xl bg-white/5 border border-white/10 hover:border-white/20 transition-all">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium text-white text-sm">{tool.name}</span>
              <span className={`text-xs px-2 py-0.5 rounded-full ${tool.dangerous ? 'bg-red-500/20 text-red-300' : 'bg-green-500/20 text-green-300'}`}>
                {tool.dangerous ? 'dangerous' : 'safe'}
              </span>
            </div>
            <p className="text-xs text-gray-400 mb-2">{tool.description}</p>
            <span className="text-xs text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded">{tool.category}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
