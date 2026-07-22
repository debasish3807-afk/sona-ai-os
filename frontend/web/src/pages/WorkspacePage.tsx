import { useState, useCallback } from "react";
import { WorkspaceLayout } from "./components/workspace/WorkspaceLayout";
import { DockablePanel } from "./components/workspace/DockablePanel";
import { AISidebar } from "./components/workspace/AISidebar";
import { ProjectExplorer } from "./components/workspace/ProjectExplorer";
import { FileExplorer } from "./components/workspace/FileExplorer";
import { IntegratedTerminal } from "./components/workspace/IntegratedTerminal";
import { CodeEditor } from "./components/workspace/CodeEditor";
import { WorkspaceTabs, Tab } from "./components/workspace/WorkspaceTabs";
import { CommandPalette } from "./components/workspace/CommandPalette";
import { GlobalSearch } from "./components/workspace/GlobalSearch";

export function WorkspacePage() {
  const [tabs, setTabs] = useState<Tab[]>([
    { id: "welcome", label: "Welcome", type: "chat" },
  ]);
  const [activeTabId, setActiveTabId] = useState<string | null>("welcome");
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  const [showGlobalSearch, setShowGlobalSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [editorFile, setEditorFile] = useState<string | null>(null);
  const [editorContent, setEditorContent] = useState("");
  const [activeFilePath, setActiveFilePath] = useState<string | null>(null);
  const [leftVisible, setLeftVisible] = useState(true);
  const [rightVisible, setRightVisible] = useState(true);
  const [bottomVisible, setBottomVisible] = useState(false);

  const handleFileSelect = useCallback((path: string) => {
    setActiveFilePath(path);
    // Check if tab already exists
    setTabs((prev) => {
      if (prev.find((t) => t.id === `file:${path}`)) return prev;
      return [...prev, { id: `file:${path}`, label: path.split("/").pop() || path, type: "file", path }];
    });
    setActiveTabId(`file:${path}`);
    // Load file content
    fetch(`/api/v1/workspace/files/content?path=${encodeURIComponent(path)}`)
      .then((r) => r.json())
      .then((data) => {
        if (data.content) setEditorContent(data.content);
        else if (data.error) setEditorContent(`// Error: ${data.error}`);
        setEditorFile(path);
      })
      .catch(() => setEditorContent("// Error loading file"));
  }, []);

  const handleCloseTab = useCallback((id: string) => {
    setTabs((prev) => {
      const idx = prev.findIndex((t) => t.id === id);
      const next = prev.filter((t) => t.id !== id);
      if (activeTabId === id && next.length > 0) {
        setActiveTabId(next[Math.min(idx, next.length - 1)].id);
      }
      return next;
    });
  }, [activeTabId]);

  const handleSendMessage = useCallback((message: string) => {
    const chatId = `chat:${Date.now()}`;
    setTabs((prev) => [...prev, { id: chatId, label: "AI Chat", type: "chat" }]);
    setActiveTabId(chatId);
  }, []);

  const commands = [
    { id: "palette", label: "Command Palette...", shortcut: "⌘K", category: "Workspace", action: () => setShowCommandPalette(true) },
    { id: "search", label: "Global Search...", shortcut: "⌘⇧F", category: "Workspace", action: () => setShowGlobalSearch(true) },
    { id: "explorer", label: "Toggle Explorer", shortcut: "⌘B", category: "View", action: () => setLeftVisible((v) => !v) },
    { id: "sidebar", label: "Toggle AI Sidebar", shortcut: "⌘⇧B", category: "View", action: () => setRightVisible((v) => !v) },
    { id: "terminal", label: "Toggle Terminal", shortcut: "⌘`", category: "View", action: () => setBottomVisible((v) => !v) },
    { id: "new-chat", label: "New Chat", shortcut: "⌘N", category: "AI", action: () => handleSendMessage("") },
    { id: "ai-explain", label: "Explain Selected Code", shortcut: "⌘⇧E", category: "AI", action: () => handleSendMessage("Explain the current file structure") },
    { id: "ai-refactor", label: "Refactor Code", shortcut: "⌘⇧R", category: "AI", action: () => handleSendMessage("Review and suggest refactoring for the current file") },
    { id: "ai-test", label: "Generate Tests", shortcut: "⌘⇧T", category: "AI", action: () => handleSendMessage("Write tests for the current module") },
    { id: "git-status", label: "Git Status", shortcut: "⌘⇧G", category: "Git", action: () => handleSendMessage("Show git status and recent changes") },
  ];

  return (
    <>
      <WorkspaceLayout
        leftPanel={
          <ProjectExplorer onFileSelect={handleFileSelect} activeFilePath={activeFilePath} />
        }
        rightPanel={
          <AISidebar onSendMessage={handleSendMessage} />
        }
        bottomPanel={
          <IntegratedTerminal defaultCwd="~" />
        }
        defaultLeftVisible={leftVisible}
        defaultRightVisible={rightVisible}
        defaultBottomVisible={bottomVisible}
        onToggleLeft={() => setLeftVisible((v) => !v)}
        onToggleRight={() => setRightVisible((v) => !v)}
        onToggleBottom={() => setBottomVisible((v) => !v)}
        topBar={
          <div className="bg-gray-900 border-b border-gray-800">
            <WorkspaceTabs tabs={tabs} activeTabId={activeTabId} onSelect={setActiveTabId} onClose={handleCloseTab} onNewTab={() => handleSendMessage("")} />
          </div>
        }
      >
        <div className="h-full flex flex-col">
          {activeTabId?.startsWith("file:") && editorFile ? (
            <CodeEditor filePath={editorFile} initialContent={editorContent} />
          ) : activeTabId === "welcome" ? (
            <div className="flex-1 flex items-center justify-center p-8">
              <div className="max-w-lg text-center">
                <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                  <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <h1 className="text-2xl font-bold text-white mb-2">Welcome to Sona AI OS</h1>
                <p className="text-gray-400 mb-6 text-sm">Your personal AI-powered development workspace</p>
                <div className="grid grid-cols-2 gap-3 text-left">
                  {[
                    { icon: "💬", title: "AI Chat", desc: "Ask questions, get answers" },
                    { icon: "📁", title: "Project Explorer", desc: "Browse and manage files" },
                    { icon: "💻", title: "Terminal", desc: "Run commands and scripts" },
                    { icon: "🔍", title: "Global Search", desc: "Find anything across files" },
                    { icon: "⚡", title: "Command Palette", desc: "Quick actions (⌘K)" },
                    { icon: "🔧", title: "AI Coding", desc: "Explain, review, refactor" },
                  ].map((item) => (
                    <div key={item.title} className="flex items-start gap-3 p-3 rounded-lg bg-gray-900 border border-gray-800 hover:border-gray-700 transition-colors cursor-pointer"
                      onClick={() => handleSendMessage(`How do I use the ${item.title} feature?`)}>
                      <span className="text-lg">{item.icon}</span>
                      <div>
                        <p className="text-sm font-medium text-gray-200">{item.title}</p>
                        <p className="text-xs text-gray-500">{item.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-6 text-xs text-gray-600">
                  Press <kbd className="px-1.5 py-0.5 bg-gray-800 rounded text-gray-400">⌘K</kbd> to open Command Palette
                </div>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-500">
              <p>Select a file or start a conversation</p>
            </div>
          )}
        </div>
      </WorkspaceLayout>
      <CommandPalette isOpen={showCommandPalette} onClose={() => setShowCommandPalette(false)} commands={commands} onSearch={setSearchQuery} />
      <GlobalSearch isOpen={showGlobalSearch} onClose={() => setShowGlobalSearch(false)} initialQuery={searchQuery} />
    </>
  );
}
