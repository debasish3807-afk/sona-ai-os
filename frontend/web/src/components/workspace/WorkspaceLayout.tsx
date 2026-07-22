import { useState, useCallback } from "react";

interface PanelConfig {
  id: string;
  position: "left" | "right" | "bottom" | "center";
  width?: number;
  height?: number;
  isVisible: boolean;
}

interface WorkspaceLayoutProps {
  children: React.ReactNode;
  leftPanel?: React.ReactNode;
  rightPanel?: React.ReactNode;
  bottomPanel?: React.ReactNode;
  leftPanelWidth?: number;
  rightPanelWidth?: number;
  bottomPanelHeight?: number;
  defaultLeftVisible?: boolean;
  defaultRightVisible?: boolean;
  defaultBottomVisible?: boolean;
  onToggleLeft?: () => void;
  onToggleRight?: () => void;
  onToggleBottom?: () => void;
  topBar?: React.ReactNode;
}

export function WorkspaceLayout({
  children, leftPanel, rightPanel, bottomPanel,
  leftPanelWidth = 280, rightPanelWidth = 320, bottomPanelHeight = 250,
  defaultLeftVisible = true, defaultRightVisible = true, defaultBottomVisible = false,
  onToggleLeft, onToggleRight, onToggleBottom,
  topBar,
}: WorkspaceLayoutProps) {
  const [leftVisible, setLeftVisible] = useState(defaultLeftVisible);
  const [rightVisible, setRightVisible] = useState(defaultRightVisible);
  const [bottomVisible, setBottomVisible] = useState(defaultBottomVisible);
  const [leftWidth, setLeftWidth] = useState(leftPanelWidth);
  const [rightWidth, setRightWidth] = useState(rightPanelWidth);
  const [bottomHeight, setBottomHeight] = useState(bottomPanelHeight);
  const [isDragging, setIsDragging] = useState<"left" | "right" | "bottom" | null>(null);

  const handleToggleLeft = useCallback(() => { setLeftVisible((v) => !v); onToggleLeft?.(); }, [onToggleLeft]);
  const handleToggleRight = useCallback(() => { setRightVisible((v) => !v); onToggleRight?.(); }, [onToggleRight]);
  const handleToggleBottom = useCallback(() => { setBottomVisible((v) => !v); onToggleBottom?.(); }, [onToggleBottom]);

  const handleMouseDown = useCallback((panel: "left" | "right" | "bottom") => (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(panel);
    const startX = e.clientX;
    const startY = e.clientY;
    const startWidth = panel === "left" ? leftWidth : rightWidth;
    const startHeight = bottomHeight;

    const handleMouseMove = (ev: MouseEvent) => {
      if (panel === "left") setLeftWidth(Math.max(180, Math.min(600, startWidth + ev.clientX - startX)));
      else if (panel === "right") setRightWidth(Math.max(180, Math.min(600, startWidth - (ev.clientX - startX))));
      else if (panel === "bottom") setBottomHeight(Math.max(100, Math.min(500, startHeight - (ev.clientY - startY))));
    };
    const handleMouseUp = () => { setIsDragging(null); document.removeEventListener("mousemove", handleMouseMove); document.removeEventListener("mouseup", handleMouseUp); };
    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
  }, [leftWidth, rightWidth, bottomHeight]);

  return (
    <div className="h-full flex flex-col bg-gray-950 text-gray-100">
      {topBar && <div className="shrink-0">{topBar}</div>}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left Panel */}
        {leftPanel && (
          <div className="shrink-0 flex" style={{ width: leftVisible ? leftWidth : 0, overflow: leftVisible ? undefined : "hidden" }}>
            <div className="flex-1 overflow-hidden border-r border-gray-800">{leftPanel}</div>
            <div className="w-1 cursor-col-resize hover:bg-blue-500 active:bg-blue-600 transition-colors" onMouseDown={handleMouseDown("left")} />
          </div>
        )}
        {/* Center / Main */}
        <div className="flex-1 flex flex-col overflow-hidden min-w-0">
          <div className="flex-1 overflow-hidden">{children}</div>
          {bottomPanel && (
            <div className="shrink-0 flex flex-col" style={{ height: bottomVisible ? bottomHeight : 0, overflow: bottomVisible ? undefined : "hidden" }}>
              <div className="w-full h-1 cursor-row-resize hover:bg-blue-500 active:bg-blue-600 transition-colors shrink-0" onMouseDown={handleMouseDown("bottom")} />
              <div className="flex-1 overflow-hidden border-t border-gray-800">{bottomPanel}</div>
            </div>
          )}
        </div>
        {/* Right Panel */}
        {rightPanel && (
          <div className="shrink-0 flex" style={{ width: rightVisible ? rightWidth : 0, overflow: rightVisible ? undefined : "hidden" }}>
            <div className="w-1 cursor-col-resize hover:bg-blue-500 active:bg-blue-600 transition-colors" onMouseDown={handleMouseDown("right")} />
            <div className="flex-1 overflow-hidden border-l border-gray-800">{rightPanel}</div>
          </div>
        )}
      </div>
      {/* Footer resize handles */}
    </div>
  );
}
