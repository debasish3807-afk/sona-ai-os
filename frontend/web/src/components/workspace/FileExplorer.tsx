import { useState, useEffect, useCallback } from "react";

interface FileItem {
  name: string;
  path: string;
  is_dir: boolean;
  size?: number;
  extension?: string;
  modified?: string;
}

interface FileExplorerProps {
  currentPath: string;
  onNavigate: (path: string) => void;
  onFileSelect: (path: string) => void;
}

export function FileExplorer({ currentPath, onNavigate, onFileSelect }: FileExplorerProps) {
  const [items, setItems] = useState<FileItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"list" | "grid">("list");
  const [sortBy, setSortBy] = useState<"name" | "type" | "size">("name");

  const loadDirectory = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/v1/workspace/files?path=${encodeURIComponent(currentPath)}&depth=1`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      setItems(sortItems(data.nodes || [], sortBy));
    } catch (err: any) {
      setError(err.message);
      // Fallback mock data
      setItems(sortItems([
        { name: "..", path: currentPath.split("/").slice(0, -1).join("/") || ".", is_dir: true },
        { name: "src", path: "src", is_dir: true },
        { name: "index.ts", path: "index.ts", is_dir: false, extension: ".ts", size: 1204 },
        { name: "README.md", path: "README.md", is_dir: false, extension: ".md", size: 3420 },
      ], sortBy));
    } finally {
      setIsLoading(false);
    }
  }, [currentPath, sortBy]);

  useEffect(() => { loadDirectory(); }, [loadDirectory]);

  const sortItems = (items: FileItem[], by: string) => {
    const sorted = [...items].sort((a, b) => {
      if (a.is_dir && !b.is_dir) return -1;
      if (!a.is_dir && b.is_dir) return 1;
      if (by === "name") return a.name.localeCompare(b.name);
      if (by === "size") return (b.size || 0) - (a.size || 0);
      return (a.extension || "").localeCompare(b.extension || "");
    });
    return sorted;
  };

  const handleItemClick = (item: FileItem) => {
    if (item.name === "..") {
      onNavigate(currentPath.split("/").slice(0, -1).join("/") || ".");
    } else if (item.is_dir) {
      onNavigate(item.path);
    } else {
      onFileSelect(item.path);
    }
  };

  const breadcrumbs = currentPath.split("/").filter(Boolean);

  return (
    <div className="flex flex-col h-full">
      {/* Breadcrumb navigation */}
      <div className="flex items-center gap-1 px-3 py-1.5 bg-gray-900 border-b border-gray-800 text-xs shrink-0 overflow-x-auto">
        <button onClick={() => onNavigate(".")} className="text-gray-400 hover:text-gray-200 whitespace-nowrap px-1 py-0.5 rounded hover:bg-gray-800">~</button>
        {breadcrumbs.map((crumb, i) => (
          <span key={i} className="flex items-center gap-1 whitespace-nowrap">
            <svg className="w-3 h-3 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
            <button onClick={() => onNavigate(breadcrumbs.slice(0, i + 1).join("/"))}
              className={`px-1 py-0.5 rounded hover:bg-gray-800 ${i === breadcrumbs.length - 1 ? "text-blue-400" : "text-gray-400 hover:text-gray-200"}`}>
              {crumb}
            </button>
          </span>
        ))}
      </div>

      {/* Toolbar */}
      <div className="flex items-center justify-between px-3 py-1 border-b border-gray-800 shrink-0">
        <div className="flex items-center gap-1">
          <button onClick={() => setViewMode("list")} className={`p-1 rounded ${viewMode === "list" ? "bg-gray-700 text-gray-200" : "text-gray-500 hover:text-gray-300"}`} title="List view">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" /></svg>
          </button>
          <button onClick={() => setViewMode("grid")} className={`p-1 rounded ${viewMode === "grid" ? "bg-gray-700 text-gray-200" : "text-gray-500 hover:text-gray-300"}`} title="Grid view">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM14 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zM14 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" /></svg>
          </button>
        </div>
        <select value={sortBy} onChange={(e) => setSortBy(e.target.value as any)}
          className="bg-transparent text-xs text-gray-400 outline-none cursor-pointer hover:text-gray-200">
          <option value="name">Name</option>
          <option value="type">Type</option>
          <option value="size">Size</option>
        </select>
      </div>

      {/* File list */}
      <div className="flex-1 overflow-y-auto">
        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}
        {error && <div className="text-center py-4 text-xs text-red-400">{error}</div>}
        {!isLoading && !error && viewMode === "list" && (
          <div className="divide-y divide-gray-800/50">
            {items.map((item) => (
              <button key={item.path} onClick={() => handleItemClick(item)}
                className="w-full flex items-center gap-3 px-3 py-2 text-sm text-left hover:bg-gray-800/50 transition-colors">
                <span className="text-base">{item.is_dir ? (item.name === ".." ? "↩️" : "📁") : "📄"}</span>
                <span className="flex-1 truncate text-gray-300">{item.name}</span>
                {item.size !== undefined && <span className="text-xs text-gray-600">{item.size > 1024 ? `${(item.size / 1024).toFixed(1)} KB` : `${item.size} B`}</span>}
                {item.is_dir && <svg className="w-3 h-3 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>}
              </button>
            ))}
          </div>
        )}
        {!isLoading && !error && viewMode === "grid" && (
          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-2 p-3">
            {items.map((item) => (
              <button key={item.path} onClick={() => handleItemClick(item)}
                className="flex flex-col items-center gap-1 p-3 rounded-lg hover:bg-gray-800/50 transition-colors text-center">
                <span className="text-2xl">{item.is_dir ? "📁" : "📄"}</span>
                <span className="text-xs text-gray-300 truncate w-full">{item.name}</span>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
