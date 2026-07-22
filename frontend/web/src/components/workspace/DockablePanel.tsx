import { useState } from "react";

interface PanelAction {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
}

interface DockablePanelProps {
  title: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
  actions?: PanelAction[];
  defaultCollapsed?: boolean;
  collapsible?: boolean;
}

export function DockablePanel({ title, icon, children, actions, defaultCollapsed = false, collapsible = true }: DockablePanelProps) {
  const [collapsed, setCollapsed] = useState(defaultCollapsed);

  return (
    <div className="flex flex-col h-full">
      {/* Panel Header */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-gray-900 border-b border-gray-800 shrink-0">
        <div className="flex items-center gap-2 min-w-0">
          {icon && <span className="shrink-0 text-gray-400">{icon}</span>}
          <span className="text-xs font-medium text-gray-300 uppercase tracking-wider truncate">{title}</span>
        </div>
        <div className="flex items-center gap-0.5">
          {actions?.map((a, i) => (
            <button key={i} onClick={a.onClick} title={a.label}
              className="p-1 rounded hover:bg-gray-700 text-gray-400 hover:text-gray-200 transition-colors">
              {a.icon}
            </button>
          ))}
          {collapsible && (
            <button onClick={() => setCollapsed((c) => !c)} className="p-1 rounded hover:bg-gray-700 text-gray-400 hover:text-gray-200 transition-colors" title={collapsed ? "Expand" : "Collapse"}>
              <svg className={`w-3.5 h-3.5 transition-transform ${collapsed ? "" : "rotate-90"}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
            </button>
          )}
        </div>
      </div>
      {/* Panel Content */}
      {!collapsed && <div className="flex-1 overflow-y-auto overflow-x-hidden">{children}</div>}
    </div>
  );
}
