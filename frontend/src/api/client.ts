const API_BASE = import.meta.env.VITE_API_BASE ?? '/api/v1';

async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    ...init,
    headers: {
      ...(init.body ? { 'Content-Type': 'application/json' } : {}),
      ...init.headers
    }
  });
  if (!response.ok) {
    const text = await response.text();
    try {
      const payload = JSON.parse(text);
      const detail = Array.isArray(payload.detail)
        ? payload.detail.map((item: { msg?: string }) => item.msg).filter(Boolean).join(', ')
        : payload.detail;
      throw new Error(detail || payload.message || text || response.statusText);
    } catch (error) {
      if (error instanceof Error && error.message !== text) throw error;
      throw new Error(text || response.statusText);
    }
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}

export async function apiGet<T>(path: string): Promise<T> {
  return apiRequest<T>(path);
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return apiRequest<T>(path, {
    method: 'POST',
    body: body === undefined ? undefined : JSON.stringify(body)
  });
}

export async function apiPatch<T>(path: string, body: unknown): Promise<T> {
  return apiRequest<T>(path, {
    method: 'PATCH',
    body: JSON.stringify(body)
  });
}

export async function apiDelete(path: string): Promise<void> {
  return apiRequest<void>(path, { method: 'DELETE' });
}

export const REPORT_DOWNLOAD_BASE = API_BASE;
