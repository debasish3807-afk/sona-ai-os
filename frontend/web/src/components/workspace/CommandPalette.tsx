import { useState, useEffect, useRef, useCallback } from "react";

interface Command {
  id: string;
  label: string;
  shortcut?: string;
  category: string;
  action: () => void;
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  commands: Command[];
  onSearch: (query: string) => void;
  recentSearches?: string[];
}

export function CommandPalette({ isOpen, onClose, commands, onSearch, recentSearches = [] }: CommandPaletteProps) {
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const filtered = query
    ? commands.filter((c) => c.label.toLowerCase().includes(query.toLowerCase()))
    : commands;

  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "ArrowDown") { e.preventDefault(); setSelectedIndex((i) => Math.min(i + 1, filtered.length - 1)); }
      else if (e.key === "ArrowUp") { e.preventDefault(); setSelectedIndex((i) => Math.max(i - 1, 0)); }
      else if (e.key === "Enter" && filtered[selectedIndex]) {
        filtered[selectedIndex].action();
        onClose();
      } else if (e.key === "Escape") onClose();
    },
    [filtered, selectedIndex, onClose]
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]" onClick={onClose}>
      <div className="fixed inset-0 bg-black/40" />
      <div
        className="relative w-full max-w-xl bg-gray-900 border border-gray-700 rounded-xl shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-700">
          <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => { setQuery(e.target.value); onSearch(e.target.value); setSelectedIndex(0); }}
            onKeyDown={handleKeyDown}
            placeholder="Search commands, files, or actions..."
            className="flex-1 bg-transparent text-white placeholder-gray-500 outline-none text-sm"
          />
          <kbd className="hidden sm:inline-flex text-xs text-gray-500 border border-gray-600 px-1.5 py-0.5 rounded">ESC</kbd>
        </div>
        {query && query.length > 2 && recentSearches.length > 0 && (
          <div className="px-4 py-2 border-b border-gray-800">
            <p className="text-xs text-gray-500 mb-1">Recent searches</p>
            <div className="flex flex-wrap gap-2">
              {recentSearches.slice(0, 5).map((s) => (
                <button key={s} onClick={() => setQuery(s)} className="text-xs text-gray-300 bg-gray-800 px-2 py-0.5 rounded hover:bg-gray-700">
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        <div className="max-h-72 overflow-y-auto">
          {filtered.map((cmd, i) => (
            <button
              key={cmd.id}
              className={`w-full flex items-center justify-between px-4 py-2.5 text-sm text-left transition-colors ${
                i === selectedIndex ? "bg-blue-600/20 text-blue-300" : "text-gray-300 hover:bg-gray-800"
              }`}
              onClick={() => { cmd.action(); onClose(); }}
              onMouseEnter={() => setSelectedIndex(i)}
            >
              <span>{cmd.label}</span>
              <span className="flex items-center gap-2">
                <span className="text-xs text-gray-500">{cmd.category}</span>
                {cmd.shortcut && <kbd className="text-xs text-gray-400 bg-gray-800 px-1.5 py-0.5 rounded">{cmd.shortcut}</kbd>}
              </span>
            </button>
          ))}
          {filtered.length === 0 && <p className="px-4 py-8 text-sm text-gray-500 text-center">No results for "{query}"</p>}
        </div>
      </div>
    </div>
  );
}
