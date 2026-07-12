import { useState } from 'react';
import { apiRequest } from '../api/client';

export function MemoryPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const search = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const data = await apiRequest<any>(`/memory/search?query=${encodeURIComponent(query)}`);
      setResults(data.results || []);
    } catch { setResults([]); }
    finally { setLoading(false); }
  };

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">Memory</h1>
      <div className="flex gap-3 mb-6">
        <input value={query} onChange={(e) => setQuery(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && search()}
          placeholder="Search memories..." className="flex-1 px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500/50" />
        <button onClick={search} disabled={loading} className="px-6 py-3 bg-blue-500/20 text-blue-300 rounded-xl hover:bg-blue-500/30 disabled:opacity-50">Search</button>
      </div>
      <div className="space-y-4">
        {results.map((r, i) => (
          <div key={i} className="p-4 rounded-xl bg-white/5 border border-white/10">
            <div className="flex justify-between mb-2">
              <span className="text-xs text-blue-400">{r.match_type}</span>
              <span className="text-xs text-gray-500">Score: {r.score}</span>
            </div>
            <p className="text-sm text-gray-300 whitespace-pre-wrap">{r.content}</p>
          </div>
        ))}
        {results.length === 0 && !loading && <p className="text-gray-500 text-center py-8">Search your knowledge base</p>}
      </div>
    </div>
  );
}
