// Thin API client. In dev VITE_API_BASE is empty and requests hit /api,
// which Vite proxies to the backend. In prod it points at the deployed API.
const BASE = import.meta.env.VITE_API_BASE ?? "";

export async function sendChat(messages, { signal } = {}) {
  const resp = await fetch(`${BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
    signal,
  });

  if (!resp.ok) {
    let detail = `Request failed (${resp.status})`;
    try {
      const body = await resp.json();
      if (body?.detail) detail = body.detail;
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail);
  }

  return resp.json(); // { reply, provider, model }
}

export async function fetchHealth() {
  const resp = await fetch(`${BASE}/api/health`);
  if (!resp.ok) throw new Error(`Health check failed (${resp.status})`);
  return resp.json(); // { status, provider, model }
}
