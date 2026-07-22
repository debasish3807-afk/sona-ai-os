import { useState, useRef, useEffect, useCallback } from "react";

interface TerminalTab {
  id: string;
  label: string;
  cwd?: string;
}

interface IntegratedTerminalProps {
  defaultCwd?: string;
  maxHistory?: number;
}

export function IntegratedTerminal({ defaultCwd = "~", maxHistory = 500 }: IntegratedTerminalProps) {
  const [tabs, setTabs] = useState<TerminalTab[]>([{ id: "1", label: "bash", cwd: defaultCwd }]);
  const [activeTab, setActiveTab] = useState("1");
  const [lines, setLines] = useState<{ text: string; type: "input" | "output" | "error" | "system" }[]>([
    { text: `Sona AI OS Terminal [${new Date().toLocaleString()}]`, type: "system" },
    { text: `Type 'help' for available commands`, type: "system" },
    { text: "", type: "output" },
  ]);
  const [input, setInput] = useState("");
  const [history, setHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [cwd, setCwd] = useState(defaultCwd);
  const [isExecuting, setIsExecuting] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [lines]);

  const executeCommand = useCallback(async (cmd: string) => {
    if (!cmd.trim()) return;
    setLines((prev) => [...prev, { text: `${cwd} $ ${cmd}`, type: "input" }]);
    setHistory((prev) => [...prev.slice(-99), cmd]);
    setHistoryIndex(-1);
    setIsExecuting(true);

    // Built-in commands
    const parts = cmd.trim().split(/\s+/);
    const base = parts[0].toLowerCase();

    if (base === "clear") {
      setLines([]);
    } else if (base === "help") {
      setLines((prev) => [...prev,
        { text: "Available commands:", type: "output" },
        { text: "  help          Show this help", type: "output" },
        { text: "  clear         Clear terminal", type: "output" },
        { text: "  pwd           Print working directory", type: "output" },
        { text: "  echo <text>   Print text", type: "output" },
        { text: "  ls [path]     List directory contents", type: "output" },
        { text: "  date          Show date/time", type: "output" },
        { text: "  whoami        Show current user", type: "output" },
        { text: "", type: "output" },
      ]);
    } else if (base === "pwd") {
      setLines((prev) => [...prev, { text: cwd, type: "output" }]);
    } else if (base === "echo") {
      setLines((prev) => [...prev, { text: parts.slice(1).join(" "), type: "output" }]);
    } else if (base === "date") {
      setLines((prev) => [...prev, { text: new Date().toString(), type: "output" }]);
    } else if (base === "whoami") {
      setLines((prev) => [...prev, { text: "user", type: "output" }]);
    } else if (base === "ls") {
      try {
        const path = parts[1] || ".";
        const res = await fetch(`/api/v1/workspace/files?path=${encodeURIComponent(path)}&depth=1`);
        if (res.ok) {
          const data = await res.json();
          if (data.nodes) {
            const listing = data.nodes.map((n: any) => n.is_dir ? `${n.name}/` : n.name).join("  ") || "(empty)";
            setLines((prev) => [...prev, { text: listing, type: "output" }]);
          }
        } else {
          setLines((prev) => [...prev, { text: `ls: cannot access '${path}': No such file or directory`, type: "error" }]);
        }
      } catch {
        setLines((prev) => [...prev, { text: "ls: connection error", type: "error" }]);
      }
    } else {
      // Try API terminal
      try {
        const res = await fetch("/api/v1/terminal", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ command: cmd, cwd, timeout: 10 }),
        });
        if (res.ok) {
          const reader = res.body?.getReader();
          if (reader) {
            const decoder = new TextDecoder();
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;
              const text = decoder.decode(value);
              for (const line of text.split("\n").filter(Boolean)) {
                try {
                  const parsed = JSON.parse(line.replace(/^data: /, ""));
                  const content = parsed.content || "";
                  if (parsed.type === "error") setLines((prev) => [...prev, { text: content, type: "error" }]);
                  else setLines((prev) => [...prev, { text: content, type: "output" }]);
                } catch { setLines((prev) => [...prev, { text: line, type: "output" }]); }
              }
            }
          }
        } else {
          setLines((prev) => [...prev, { text: `Command failed with HTTP ${res.status}`, type: "error" }]);
        }
      } catch (err: any) {
        setLines((prev) => [...prev, { text: `Error: ${err.message}`, type: "error" }]);
      }
    }
    setIsExecuting(false);
  }, [cwd]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      executeCommand(input);
      setInput("");
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      if (history.length > 0) {
        const newIdx = historyIndex === -1 ? history.length - 1 : Math.max(0, historyIndex - 1);
        setHistoryIndex(newIdx);
        setInput(history[newIdx]);
      }
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      if (historyIndex >= 0) {
        const newIdx = historyIndex + 1;
        if (newIdx >= history.length) { setHistoryIndex(-1); setInput(""); }
        else { setHistoryIndex(newIdx); setInput(history[newIdx]); }
      }
    }
  };

  const tabIcons: Record<string, string> = { bash: ">_", python: ">>>", node: "==", git: "±" };

  return (
    <div className="flex flex-col h-full bg-gray-950">
      {/* Terminal tabs */}
      <div className="flex items-center bg-gray-900 border-b border-gray-800 overflow-x-auto shrink-0">
        {tabs.map((tab) => (
          <div key={tab.id}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs cursor-pointer border-r border-gray-800 transition-colors ${
              tab.id === activeTab ? "bg-gray-950 text-white border-t-2 border-t-green-500" : "text-gray-500 hover:text-gray-300 hover:bg-gray-850"
            }`}
            onClick={() => setActiveTab(tab.id)}
          >
            <span className="font-mono">{tabIcons[tab.label] || "$"}</span>
            <span>{tab.label}</span>
            <button onClick={(e) => { e.stopPropagation(); if (tabs.length > 1) setTabs((t) => t.filter((x) => x.id !== tab.id)); }}
              className="ml-1 p-0.5 rounded hover:bg-gray-700 opacity-0 hover:opacity-100 transition-opacity">
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
          </div>
        ))}
        <button onClick={() => {
          const id = String(Date.now());
          setTabs((t) => [...t, { id, label: "bash", cwd: defaultCwd }]);
          setActiveTab(id);
        }} className="px-2 py-1.5 text-gray-500 hover:text-gray-300 transition-colors" title="New terminal">
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
        </button>
      </div>
      {/* Output */}
      <div className="flex-1 overflow-y-auto p-3 font-mono text-xs leading-relaxed" onClick={() => inputRef.current?.focus()}>
        {lines.map((line, i) => (
          <div key={i} className={`whitespace-pre-wrap break-all ${
            line.type === "error" ? "text-red-400" :
            line.type === "input" ? "text-green-300" :
            line.type === "system" ? "text-gray-500 italic" : "text-gray-300"
          }`}>{line.text || "\u00A0"}</div>
        ))}
        <div ref={endRef} />
      </div>
      {/* Input line */}
      <div className="flex items-center gap-2 px-3 py-2 border-t border-gray-800 shrink-0">
        <span className="font-mono text-xs text-green-400 whitespace-nowrap">{cwd} $</span>
        <input ref={inputRef} type="text" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={handleKeyDown}
          disabled={isExecuting}
          placeholder={isExecuting ? "Running..." : "Type a command..."}
          className="flex-1 bg-transparent text-white font-mono text-xs outline-none placeholder-gray-600" />
        <button onClick={() => { setLines([]); }} className="p-1 rounded hover:bg-gray-800 text-gray-500 hover:text-gray-300 transition-colors" title="Clear">
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
        </button>
      </div>
    </div>
  );
}
