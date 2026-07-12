import { useState, useRef, useEffect } from 'react';
import { streamRequest } from '../api/client';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || streaming) return;
    const userMsg: Message = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setStreaming(true);

    const assistantMsg: Message = { role: 'assistant', content: '' };
    setMessages((prev) => [...prev, assistantMsg]);

    try {
      await streamRequest('/chat/stream', {
        messages: [...messages, userMsg].map((m) => ({ role: m.role, content: m.content })),
      }, (data) => {
        try {
          const parsed = JSON.parse(data);
          if (parsed.event === 'delta' && parsed.content) {
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              if (last.role === 'assistant') last.content += parsed.content;
              return [...updated];
            });
          }
        } catch { /* skip unparseable */ }
      });
    } catch (err) {
      setMessages((prev) => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last.role === 'assistant') last.content = 'Error: Failed to get response';
        return [...updated];
      });
    } finally {
      setStreaming(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-auto p-6 space-y-4">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <p className="text-4xl mb-4">🧠</p>
              <p className="text-xl font-medium">Start a conversation with Sona</p>
              <p className="text-sm mt-2">Your Personal AI Engineer</p>
            </div>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] p-4 rounded-2xl ${
              msg.role === 'user'
                ? 'bg-blue-500/20 border border-blue-500/30 text-blue-100'
                : 'bg-white/5 border border-white/10 text-gray-200'
            }`}>
              <pre className="whitespace-pre-wrap font-sans text-sm">{msg.content || '...'}</pre>
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      {/* Input */}
      <div className="p-4 border-t border-white/5 bg-gray-900/50">
        <div className="flex gap-3 max-w-4xl mx-auto">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
            placeholder="Ask Sona anything..."
            className="flex-1 px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500/50"
            disabled={streaming}
          />
          <button onClick={sendMessage} disabled={streaming || !input.trim()}
            className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white font-medium rounded-xl hover:opacity-90 disabled:opacity-50 transition-all">
            {streaming ? '...' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  );
}
