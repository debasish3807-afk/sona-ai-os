import { useRef, useState, useCallback, useEffect } from "react";

export interface Tab {
  id: string;
  label: string;
  type: "chat" | "file" | "terminal" | "explorer" | "editor" | "settings" | "search";
  icon?: string;
  isDirty?: boolean;
  path?: string;
}

interface WorkspaceTabsProps {
  tabs: Tab[];
  activeTabId: string | null;
  onSelect: (id: string) => void;
  onClose: (id: string) => void;
  onReorder?: (fromIndex: number, toIndex: number) => void;
  onNewTab?: () => void;
}

export function WorkspaceTabs({ tabs, activeTabId, onSelect, onClose, onReorder, onNewTab }: WorkspaceTabsProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dragIndex, setDragIndex] = useState<number | null>(null);

  const handleDragStart = (e: React.DragEvent, index: number) => {
    setDragIndex(index);
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", String(index));
  };

  const handleDrop = useCallback((e: React.DragEvent, toIndex: number) => {
    e.preventDefault();
    if (dragIndex !== null && dragIndex !== toIndex && onReorder) {
      onReorder(dragIndex, toIndex);
    }
    setDragIndex(null);
  }, [dragIndex, onReorder]);

  if (tabs.length === 0) return null;

  return (
    <div className="flex items-center bg-gray-900 border-b border-gray-700 overflow-x-auto scrollbar-none" ref={containerRef}>
      {tabs.map((tab, i) => (
        <div key={tab.id}
          draggable
          onDragStart={(e) => handleDragStart(e, i)}
          onDragOver={(e) => { e.preventDefault(); e.dataTransfer.dropEffect = "move"; }}
          onDrop={(e) => handleDrop(e, i)}
          className={`group flex items-center gap-1.5 px-3 py-1.5 text-xs cursor-pointer select-none border-r border-gray-700 min-w-0 transition-colors ${
            tab.id === activeTabId
              ? "bg-gray-800 text-white border-t-2 border-t-blue-500"
              : "text-gray-400 hover:bg-gray-800/50 hover:text-gray-300"
          }`}
          onClick={() => onSelect(tab.id)}
        >
          {tab.type === "chat" && <svg className="w-3.5 h-3.5 text-purple-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" /></svg>}
          {tab.type === "file" && <svg className="w-3.5 h-3.5 text-blue-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>}
          {tab.type === "terminal" && <svg className="w-3.5 h-3.5 text-green-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>}
          {tab.type === "editor" && <svg className="w-3.5 h-3.5 text-yellow-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" /></svg>}
          {tab.type === "explorer" && <svg className="w-3.5 h-3.5 text-cyan-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" /></svg>}
          {tab.type === "search" && <svg className="w-3.5 h-3.5 text-indigo-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>}

          <span className="truncate max-w-[120px]">{tab.label}</span>
          {tab.isDirty && <span className="w-2 h-2 rounded-full bg-yellow-400 shrink-0" />}
          <button
            onClick={(e) => { e.stopPropagation(); onClose(tab.id); }}
            className="ml-1 p-0.5 rounded opacity-0 group-hover:opacity-100 hover:bg-gray-700 transition-opacity shrink-0"
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>
      ))}
      {onNewTab && (
        <button onClick={onNewTab} className="px-2 py-1.5 text-gray-500 hover:text-gray-300 hover:bg-gray-800 transition-colors" title="New tab">
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
        </button>
      )}
    </div>
  );
}
