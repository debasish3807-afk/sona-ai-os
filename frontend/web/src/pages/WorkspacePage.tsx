/**
 * Desktop AI Workspace — Main workspace page with resizable panels.
 *
 * Layout: Sidebar | Main Panel (Chat/Research/Memory) | Right Panel (Files/Terminal)
 */
import { useState, useCallback } from 'react'

// ─── Types ──────────────────────────────────────────────────────────────────

interface Message {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp?: number
}

interface FileNode {
  name: string
  path: string
  is_dir: boolean
  size?: number
  extension?: string
  children?: FileNode[]
}

interface Conversation {
  id: string
  title: string
  created_at: string
  message_count: number
  pinned: boolean
}

type PanelView = 'chat' | 'research' | 'memory' | 'rag' | 'settings'
type RightPanel = 'files' | 'terminal' | 'github'

// ─── API Client ─────────────────────────────────────────────────────────────

const API_BASE = '/workspace'

async function apiPost(path: string, body: object) {
  const resp = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return resp.json()
}

async function apiGet(path: string) {
  const resp = await fetch(`${API_BASE}${path}`)
  return resp.json()
}

// ─── Chat Panel ─────────────────────────────────────────────────────────────

function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [streaming, setStreaming] = useState(false)

  const sendMessage = useCallback(async () => {
    if (!input.trim() || loading) return

    const userMsg: Message = { role: 'user', content: input, timestamp: Date.now() }
    const newMessages = [...messages, userMsg]
    setMessages(newMessages)
    setInput('')
    setLoading(true)
    setStreaming(true)

    try {
      const resp = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: newMessages.map(m => ({ role: m.role, content: m.content })),
          stream: true,
        }),
      })

      const reader = resp.body?.getReader()
      const decoder = new TextDecoder()
      let assistantContent = ''

      if (reader) {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          const text = decoder.decode(value)
          const lines = text.split('\n')
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6))
                if (data.type === 'chunk') {
                  assistantContent += data.content
                  setMessages([...newMessages, { role: 'assistant', content: assistantContent }])
                }
              } catch { /* skip malformed */ }
            }
          }
        }
      }

      if (!assistantContent) {
        // Fallback to non-streaming
        const data = await apiPost('/chat/complete', {
          messages: newMessages.map(m => ({ role: m.role, content: m.content })),
        })
        assistantContent = data.content || '[No response]'
      }

      setMessages([...newMessages, { role: 'assistant', content: assistantContent, timestamp: Date.now() }])
    } catch (err) {
      setMessages([...newMessages, { role: 'assistant', content: `Error: ${err}` }])
    } finally {
      setLoading(false)
      setStreaming(false)
    }
  }, [input, messages, loading])

  return (
    <div className="panel chat-panel">
      <div className="panel-header">
        <h3>AI Chat</h3>
        {streaming && <span className="badge">Streaming...</span>}
      </div>
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <div className="message-role">{msg.role === 'user' ? '👤' : '🤖'}</div>
            <div className="message-content">
              <pre>{msg.content}</pre>
            </div>
          </div>
        ))}
      </div>
      <div className="chat-input">
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() } }}
          placeholder="Ask Sona anything..."
          disabled={loading}
        />
        <button onClick={sendMessage} disabled={loading || !input.trim()}>
          {loading ? '⏳' : '▶'}
        </button>
      </div>
    </div>
  )
}

// ─── Research Panel ─────────────────────────────────────────────────────────

function ResearchPanel() {
  const [query, setQuery] = useState('')
  const [report, setReport] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState('')

  const runResearch = async () => {
    if (!query.trim()) return
    setLoading(true)
    setReport(null)
    setStatus('Starting research...')

    try {
      const resp = await fetch(`${API_BASE}/research?query=${encodeURIComponent(query)}&offline=false`, {
        method: 'POST',
      })
      const reader = resp.body?.getReader()
      const decoder = new TextDecoder()

      if (reader) {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          const text = decoder.decode(value)
          for (const line of text.split('\n')) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6))
                if (data.type === 'status') setStatus(data.content)
                if (data.type === 'report') setReport(data)
                if (data.type === 'done') setStatus('Complete')
              } catch { /* skip */ }
            }
          }
        }
      }
    } catch (err) {
      setStatus(`Error: ${err}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="panel research-panel">
      <div className="panel-header"><h3>Deep Research</h3></div>
      <div className="research-input">
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') runResearch() }}
          placeholder="Research topic..."
          disabled={loading}
        />
        <button onClick={runResearch} disabled={loading}>
          {loading ? '🔍...' : '🔍 Research'}
        </button>
      </div>
      {status && <div className="status-bar">{status}</div>}
      {report && (
        <div className="report">
          <h4>{report.title}</h4>
          <p className="confidence">Confidence: {(report.confidence * 100).toFixed(0)}%</p>
          <p>{report.summary}</p>
          <h5>Sources ({report.source_count})</h5>
          <ul className="sources">
            {report.references?.map((ref: any, i: number) => (
              <li key={i}>
                <a href={ref.url} target="_blank" rel="noreferrer">{ref.title}</a>
                <span className="source-kind">{ref.source_kind}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

// ─── Memory Panel ───────────────────────────────────────────────────────────

function MemoryPanel() {
  const [memories, setMemories] = useState<any[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [newMemory, setNewMemory] = useState('')

  const loadMemories = async () => {
    const params = searchQuery ? `?query=${encodeURIComponent(searchQuery)}` : ''
    const data = await apiGet(`/memory${params}`)
    setMemories(data.memories || [])
  }

  const storeMemory = async () => {
    if (!newMemory.trim()) return
    await apiPost('/memory', { content: newMemory, memory_type: 'conversation' })
    setNewMemory('')
    loadMemories()
  }

  return (
    <div className="panel memory-panel">
      <div className="panel-header"><h3>Memory</h3></div>
      <div className="memory-controls">
        <input
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          placeholder="Search memory..."
          onKeyDown={e => { if (e.key === 'Enter') loadMemories() }}
        />
        <button onClick={loadMemories}>Search</button>
      </div>
      <div className="memory-add">
        <textarea value={newMemory} onChange={e => setNewMemory(e.target.value)} placeholder="Store new memory..." />
        <button onClick={storeMemory}>Store</button>
      </div>
      <div className="memory-list">
        {memories.map((m, i) => (
          <div key={i} className="memory-item">
            <span className="memory-type">{m.type}</span>
            <p>{m.content}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── File Explorer ──────────────────────────────────────────────────────────

function FileExplorer() {
  const [files, setFiles] = useState<FileNode[]>([])
  const [content, setContent] = useState('')
  const [selectedFile, setSelectedFile] = useState('')

  const loadFiles = async (path = '') => {
    const data = await apiGet(`/files?path=${encodeURIComponent(path)}&depth=2`)
    setFiles(data.nodes || [])
  }

  const openFile = async (path: string) => {
    const data = await apiGet(`/files/content?path=${encodeURIComponent(path)}`)
    if (data.content) {
      setContent(data.content)
      setSelectedFile(path)
    }
  }

  useState(() => { loadFiles() })

  return (
    <div className="panel file-panel">
      <div className="panel-header"><h3>Files</h3></div>
      <div className="file-tree">
        {files.map((node, i) => (
          <div key={i} className={`file-node ${node.is_dir ? 'dir' : 'file'}`}>
            {node.is_dir ? (
              <span onClick={() => loadFiles(node.path)}>📁 {node.name}</span>
            ) : (
              <span onClick={() => openFile(node.path)}>📄 {node.name}</span>
            )}
          </div>
        ))}
      </div>
      {content && (
        <div className="file-content">
          <div className="file-path">{selectedFile}</div>
          <pre><code>{content}</code></pre>
        </div>
      )}
    </div>
  )
}

// ─── Terminal Panel ─────────────────────────────────────────────────────────

function TerminalPanel() {
  const [command, setCommand] = useState('')
  const [output, setOutput] = useState('')
  const [running, setRunning] = useState(false)

  const executeCommand = async () => {
    if (!command.trim() || running) return
    setRunning(true)
    setOutput('')

    try {
      const resp = await fetch(`${API_BASE}/terminal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command, timeout: 30 }),
      })
      const reader = resp.body?.getReader()
      const decoder = new TextDecoder()
      let fullOutput = `$ ${command}\n`

      if (reader) {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          const text = decoder.decode(value)
          for (const line of text.split('\n')) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6))
                if (data.type === 'stdout' || data.type === 'stderr') {
                  fullOutput += data.content
                  setOutput(fullOutput)
                }
                if (data.type === 'exit') {
                  fullOutput += `\n[exit: ${data.code}]`
                  setOutput(fullOutput)
                }
              } catch { /* skip */ }
            }
          }
        }
      }
    } catch (err) {
      setOutput(`Error: ${err}`)
    } finally {
      setRunning(false)
      setCommand('')
    }
  }

  return (
    <div className="panel terminal-panel">
      <div className="panel-header"><h3>Terminal</h3></div>
      <div className="terminal-output">
        <pre>{output || 'Ready.'}</pre>
      </div>
      <div className="terminal-input">
        <span className="prompt">$</span>
        <input
          value={command}
          onChange={e => setCommand(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') executeCommand() }}
          placeholder="Enter command..."
          disabled={running}
        />
        {running && <button onClick={() => setRunning(false)}>⏹ Stop</button>}
      </div>
    </div>
  )
}

// ─── Settings Panel ─────────────────────────────────────────────────────────

function SettingsPanel() {
  const [settings, setSettings] = useState<any>({})
  const [loaded, setLoaded] = useState(false)

  const loadSettings = async () => {
    const data = await apiGet('/settings')
    setSettings(data)
    setLoaded(true)
  }

  const updateSetting = async (key: string, value: any) => {
    const updated = { ...settings, [key]: value }
    setSettings(updated)
    await fetch(`${API_BASE}/settings`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ [key]: value }),
    })
  }

  if (!loaded) loadSettings()

  return (
    <div className="panel settings-panel">
      <div className="panel-header"><h3>Settings</h3></div>
      <div className="settings-form">
        <label>
          AI Provider
          <select value={settings.provider || 'ollama'} onChange={e => updateSetting('provider', e.target.value)}>
            <option value="ollama">Ollama (Local)</option>
            <option value="gemini">Gemini (Free)</option>
          </select>
        </label>
        <label>
          Model
          <input value={settings.model || ''} onChange={e => updateSetting('model', e.target.value)} />
        </label>
        <label>
          Theme
          <select value={settings.theme || 'dark'} onChange={e => updateSetting('theme', e.target.value)}>
            <option value="dark">Dark</option>
            <option value="light">Light</option>
          </select>
        </label>
        <label>
          Temperature: {settings.temperature || 0.7}
          <input type="range" min="0" max="1" step="0.1"
            value={settings.temperature || 0.7}
            onChange={e => updateSetting('temperature', parseFloat(e.target.value))} />
        </label>
        <label>
          Research Depth
          <select value={settings.research_depth || 'standard'} onChange={e => updateSetting('research_depth', e.target.value)}>
            <option value="quick">Quick</option>
            <option value="standard">Standard</option>
            <option value="deep">Deep</option>
          </select>
        </label>
      </div>
    </div>
  )
}

// ─── Main Workspace Layout ──────────────────────────────────────────────────

export default function WorkspacePage() {
  const [activePanel, setActivePanel] = useState<PanelView>('chat')
  const [rightPanel, setRightPanel] = useState<RightPanel>('files')

  const renderMainPanel = () => {
    switch (activePanel) {
      case 'chat': return <ChatPanel />
      case 'research': return <ResearchPanel />
      case 'memory': return <MemoryPanel />
      case 'settings': return <SettingsPanel />
      default: return <ChatPanel />
    }
  }

  const renderRightPanel = () => {
    switch (rightPanel) {
      case 'files': return <FileExplorer />
      case 'terminal': return <TerminalPanel />
      default: return <FileExplorer />
    }
  }

  return (
    <div className="workspace">
      {/* Sidebar Navigation */}
      <nav className="workspace-sidebar">
        <button className={activePanel === 'chat' ? 'active' : ''} onClick={() => setActivePanel('chat')} title="AI Chat">💬</button>
        <button className={activePanel === 'research' ? 'active' : ''} onClick={() => setActivePanel('research')} title="Deep Research">🔬</button>
        <button className={activePanel === 'memory' ? 'active' : ''} onClick={() => setActivePanel('memory')} title="Memory">🧠</button>
        <button className={activePanel === 'settings' ? 'active' : ''} onClick={() => setActivePanel('settings')} title="Settings">⚙️</button>
        <div className="sidebar-divider" />
        <button className={rightPanel === 'files' ? 'active' : ''} onClick={() => setRightPanel('files')} title="Files">📁</button>
        <button className={rightPanel === 'terminal' ? 'active' : ''} onClick={() => setRightPanel('terminal')} title="Terminal">🖥️</button>
      </nav>

      {/* Main Panel */}
      <main className="workspace-main">
        {renderMainPanel()}
      </main>

      {/* Right Panel */}
      <aside className="workspace-right">
        {renderRightPanel()}
      </aside>
    </div>
  )
}
