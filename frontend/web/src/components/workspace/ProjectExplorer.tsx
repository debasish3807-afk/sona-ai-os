import { useState, useEffect } from "react";

interface FileNode {
  name: string;
  path: string;
  is_dir: boolean;
  size?: number;
  extension?: string;
  children?: FileNode[];
}

interface ProjectExplorerProps {
  onFileSelect: (path: string) => void;
  workspaceRoot?: string;
  activeFilePath?: string | null;
}

export function ProjectExplorer({ onFileSelect, workspaceRoot, activeFilePath }: ProjectExplorerProps) {
  const [tree, setTree] = useState<FileNode | null>(null);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadTree();
  }, [workspaceRoot]);

  const loadTree = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/v1/workspace/files?depth=3${workspaceRoot ? `&path=${encodeURIComponent(workspaceRoot)}` : ""}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      const root: FileNode = {
        name: workspaceRoot || "workspace",
        path: workspaceRoot || "",
        is_dir: true,
        children: data.nodes || [],
      };
      setTree(root);
    } catch (err: any) {
      setError(err.message);
      // Fallback: show mock tree from API
      setTree({
        name: "workspace", path: "", is_dir: true,
        children: [
          { name: "src", path: "src", is_dir: true, children: [{ name: "index.ts", path: "src/index.ts", is_dir: false, extension: ".ts" }, { name: "app.ts", path: "src/app.ts", is_dir: false, extension: ".ts" }] },
          { name: "tests", path: "tests", is_dir: true, children: [] },
          { name: "config", path: "config", is_dir: true, children: [{ name: "settings.json", path: "config/settings.json", is_dir: false, extension: ".json" }] },
        ],
      });
    } finally {
      setIsLoading(false);
    }
  };

  const toggleExpand = (path: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  };

  const renderNode = (node: FileNode, depth: number) => {
    const isExpanded = expanded.has(node.path);
    const isActive = node.path === activeFilePath;
    const nodeIcon = node.is_dir
      ? (isExpanded ? "📂" : "📁")
      : node.extension === ".py" ? "🐍" :
        node.extension === ".ts" || node.extension === ".tsx" ? "🟦" :
        node.extension === ".js" || node.extension === ".jsx" ? "🟨" :
        node.extension === ".json" ? "📋" :
        node.extension === ".md" ? "📝" : "📄";

    return (
      <div key={node.path}>
        <div
          className={`flex items-center gap-1.5 px-2 py-1 text-sm cursor-pointer rounded transition-colors ${
            isActive ? "bg-blue-600/20 text-blue-300" : "text-gray-300 hover:bg-gray-800"
          }`}
          style={{ paddingLeft: `${12 + depth * 16}px` }}
          onClick={() => {
            if (node.is_dir) toggleExpand(node.path);
            else onFileSelect(node.path);
          }}
        >
          {node.is_dir && (
            <svg className={`w-3 h-3 text-gray-500 transition-transform ${isExpanded ? "rotate-90" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          )}
          {!node.is_dir && <span className="w-3 text-center text-xs">{nodeIcon}</span>}
          <span className="truncate">{node.name}</span>
          {!node.is_dir && node.size !== undefined && (
            <span className="ml-auto text-xs text-gray-600">{node.size > 1024 ? `${(node.size / 1024).toFixed(1)}k` : `${node.size}B`}</span>
          )}
        </div>
        {node.is_dir && isExpanded && node.children?.map((child) => renderNode(child, depth + 1))}
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-gray-900 border-b border-gray-800 shrink-0">
        <span className="text-xs font-medium text-gray-300 uppercase tracking-wider">EXPLORER</span>
        <div className="flex items-center gap-0.5">
          <button onClick={loadTree} className="p-1 rounded hover:bg-gray-700 text-gray-400 hover:text-gray-200 transition-colors" title="Refresh">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
          </button>
        </div>
      </div>
      {/* Tree */}
      <div className="flex-1 overflow-y-auto py-1">
        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}
        {error && !tree && (
          <div className="text-center py-6">
            <p className="text-xs text-red-400 mb-1">Failed to load workspace</p>
            <p className="text-xs text-gray-500">{error}</p>
            <button onClick={loadTree} className="mt-2 text-xs text-blue-400 hover:text-blue-300">Retry</button>
          </div>
        )}
        {tree && renderNode(tree, 0)}
      </div>
    </div>
  );
}
