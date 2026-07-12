import { useState } from 'react';
import { apiRequest } from '../api/client';

export function DocumentsPage() {
  const [content, setContent] = useState('');
  const [title, setTitle] = useState('');
  const [status, setStatus] = useState('');

  const upload = async () => {
    if (!content.trim()) return;
    try {
      const data = await apiRequest<any>('/documents/upload', {
        method: 'POST',
        body: JSON.stringify({ content, title, doc_type: 'text' }),
      });
      setStatus(`Uploaded: ${data.chunks_created} chunks, ${data.token_count} tokens`);
      setContent('');
      setTitle('');
    } catch (err: any) { setStatus(`Error: ${err.message}`); }
  };

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">Documents</h1>
      <div className="max-w-2xl space-y-4">
        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Document title"
          className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500/50" />
        <textarea value={content} onChange={(e) => setContent(e.target.value)} placeholder="Paste document content..." rows={12}
          className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500/50 resize-none" />
        <button onClick={upload} className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl hover:opacity-90">Upload</button>
        {status && <p className="text-sm text-green-400">{status}</p>}
      </div>
    </div>
  );
}
