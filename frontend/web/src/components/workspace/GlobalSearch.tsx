import { useState, useEffect, useRef } from "react";

interface SearchResult {
  type: "file" | "code" | "chat" | "memory" | "command";
  label: string;
  description: string;
  path?: string;
  action: () => void;
}

interface GlobalSearchProps {
  isOpen: boolean;
  onClose: () => void;
  initialQuery?: string;
}

export function GlobalSearch({ isOpen, onClose, initialQuery = "" }: GlobalSearchProps) {
  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [activeIndex, setActiveIndex] = useState(0);
  const [isSearching, setIsSearching] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      setQuery(initialQuery);
      setActiveIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen, initialQuery]);

  useEffect(() => {
    if (!query || query.length < 2) { setResults([]); return; }
    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const res = await fetch(`/api/v1/search?q=${encodeURIComponent(query)}&limit=10`);
        if (res.ok) {
          const data = await res.json();
          setResults((data.results || []).map((r: any) => ({
            type: r.type || "file",
            label: r.label || r.title || r.name || query,
            description: r.description || r.snippet || "",
            path: r.path || r.url || "",
            action: () => { window.location.href = r.path || "/"; },
          })));
        }
      } catch {
        // fallback: show local results
      } finally {
        setIsSearching(false);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  // Add default local results when no network results
  const displayResults = results.length > 0 ? results : query.length >= 2
    ? [
        { type: "file" as const, label: `Search files for "${query}"`, description: "Search workspace files", action: () => {}, path: "" },
        { type: "memory" as const, label: `Search memory for "${query}"`, description: "Search stored memories", action: () => {}, path: "" },
        { type: "chat" as const, label: `Ask AI about "${query}"`, description: "Start a conversation", action: () => {}, path: "" },
      ]
    : [];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[10vh]" onClick={onClose}>
      <div className="fixed inset-0 bg-black/50" />
      <div className="relative w-full max-w-2xl bg-gray-900 border border-gray-700 rounded-xl shadow-2xl overflow-hidden" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-700">
          <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input ref={inputRef} type="text" value={query} onChange={(e) => setQuery(e.target.value)}
            placeholder="Search files, code, memories, commands..." className="flex-1 bg-transparent text-white placeholder-gray-500 outline-none text-sm" />
          {isSearching && <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />}
        </div>
        <div className="max-h-80 overflow-y-auto">
          {displayResults.map((result, i) => (
            <button key={i} className={`w-full flex items-start gap-3 px-4 py-3 text-left transition-colors ${
              i === activeIndex ? "bg-blue-600/20" : "hover:bg-gray-800"
            }`} onClick={() => { result.action(); onClose(); }}
            onMouseEnter={() => setActiveIndex(i)}>
              <span className={`mt-0.5 text-xs font-medium px-1.5 py-0.5 rounded ${
                result.type === "file" ? "bg-green-800 text-green-200" :
                result.type === "code" ? "bg-blue-800 text-blue-200" :
                result.type === "chat" ? "bg-purple-800 text-purple-200" :
                result.type === "memory" ? "bg-amber-800 text-amber-200" : "bg-gray-700 text-gray-200"
              }`}>{result.type}</span>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-white truncate">{result.label}</p>
                <p className="text-xs text-gray-400 truncate">{result.description}</p>
              </div>
              {result.path && <span className="text-xs text-gray-500 truncate max-w-[150px] hidden md:block">{result.path}</span>}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
