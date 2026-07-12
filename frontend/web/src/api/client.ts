const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = JSON.parse(localStorage.getItem('sona-auth') || '{}')?.state?.accessToken;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers as Record<string, string> || {}),
  };
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (response.status === 401) {
    // Token expired — attempt refresh or redirect
    window.dispatchEvent(new CustomEvent('auth:expired'));
  }
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || error.message || 'API request failed');
  }
  return response.json();
}

export async function streamRequest(
  path: string,
  body: unknown,
  onChunk: (data: string) => void
): Promise<void> {
  const token = JSON.parse(localStorage.getItem('sona-auth') || '{}')?.state?.accessToken;
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  });
  if (!response.ok || !response.body) throw new Error('Stream failed');
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const text = decoder.decode(value);
    for (const line of text.split('\n')) {
      if (line.startsWith('data: ') && line !== 'data: [DONE]') {
        onChunk(line.slice(6));
      }
    }
  }
}
