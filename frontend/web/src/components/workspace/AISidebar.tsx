import { useState } from "react";

interface AISidebarProps {
  onSendMessage: (message: string) => void;
  onInsertCode?: (code: string) => void;
  isLoading?: boolean;
}

export function AISidebar({ onSendMessage, onInsertCode, isLoading }: AISidebarProps) {
  const [input, setInput] = useState("");
  const [mode, setMode] = useState<"chat" | "explain" | "generate" | "review">("chat");
  const [history, setHistory] = useState<{ role: "user" | "assistant"; content: string }[]>([]);

  const handleSend = () => {
    if (!input.trim() || isLoading) return;
    setHistory((h) => [...h, { role: "user", content: input }]);
    onSendMessage(input);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  const quickActions = [
    { id: "explain", label: "Explain Code", icon: "💡", mode: "explain" as const },
    { id: "generate", label: "Generate Code", icon: "✨", mode: "generate" as const },
    { id: "review", label: "Review", icon: "🔍", mode: "review" as const },
  ];

  return (
    <div className="flex flex-col h-full bg-gray-900">
      {/* Mode selector */}
      <div className="flex items-center gap-1 px-2 py-2 border-b border-gray-800">
        <button onClick={() => setMode("chat")} className={`flex-1 text-xs py-1 rounded transition-colors ${mode === "chat" ? "bg-blue-600 text-white" : "text-gray-400 hover:text-gray-200"}`}>
          <svg className="w-3.5 h-3.5 mx-auto mb-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" /></svg>
          Chat
        </button>
        {quickActions.map((a) => (
          <button key={a.id} onClick={() => setMode(a.mode)} className={`flex-1 text-xs py-1 rounded transition-colors ${mode === a.mode ? "bg-blue-600 text-white" : "text-gray-400 hover:text-gray-200"}`}>
            <span className="block text-sm mb-0.5">{a.icon}</span>
            {a.label}
          </button>
        ))}
      </div>
      
      {/* Chat history */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-3">
        {history.length === 0 && mode === "chat" && (
          <div className="text-center py-8">
            <svg className="w-10 h-10 mx-auto text-gray-600 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
            <p className="text-xs text-gray-500">Ask the AI assistant anything</p>
          </div>
        )}
        {history.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
              msg.role === "user" ? "bg-blue-600 text-white" : "bg-gray-800 text-gray-200"
            }`}>
              {msg.role === "assistant" && (
                <div className="flex items-center gap-1.5 mb-1 text-xs text-gray-400">
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                  AI Assistant
                </div>
              )}
              <p className="whitespace-pre-wrap break-words">{msg.content}</p>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-800 rounded-lg px-3 py-2 text-sm text-gray-400">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-2 border-t border-gray-800">
        {mode !== "chat" && (
          <div className="mb-2 text-xs text-gray-500 bg-gray-800 rounded px-2 py-1">
            {mode === "explain" && "💡 Select code in the editor and I'll explain it"}
            {mode === "generate" && "✨ Describe what you want me to generate"}
            {mode === "review" && "🔍 Select code and I'll review it for issues"}
          </div>
        )}
        <div className="flex gap-2">
          <input type="text" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={handleKeyDown}
            placeholder={mode === "chat" ? "Ask anything..." : "Describe what you need..."}
            className="flex-1 bg-gray-800 text-white text-sm rounded-lg px-3 py-2 outline-none focus:ring-1 focus:ring-blue-500 placeholder-gray-500" />
          <button onClick={handleSend} disabled={isLoading || !input.trim()}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white rounded-lg px-3 py-2 transition-colors">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19V5m0 0l-7 7m7-7l7 7" /></svg>
          </button>
        </div>
      </div>
    </div>
  );
}
