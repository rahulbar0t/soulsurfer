const API_BASE = '/api';

export async function uploadVideo(file, surferName, skillLevel) {
  const formData = new FormData();
  formData.append('video', file);
  if (surferName) formData.append('surfer_name', surferName);
  if (skillLevel) formData.append('skill_level', skillLevel);

  const res = await fetch(`${API_BASE}/sessions/`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `Upload failed (${res.status})`);
  }

  return res.json();
}

export async function getSession(sessionId) {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}`);

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `Failed to fetch session (${res.status})`);
  }

  return res.json();
}

export async function sendChat(sessionId, message) {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `Chat failed (${res.status})`);
  }

  return res.json();
}

export async function checkHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('API is not available');
  return res.json();
}
