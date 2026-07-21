/**
 * Shared API client for the ScoobyBench backend.
 *
 * Prefers the Electron preload bridge (window.electronAPI) when present,
 * and falls back to direct fetch calls so the renderer also works in a
 * plain browser during development.
 */

export const API_BASE = (typeof window !== 'undefined' && window.electronAPI?.getApiUrl)
  ? window.electronAPI.getApiUrl()
  : 'http://127.0.0.1:8472';

async function parseResponse(response) {
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      if (body?.detail) detail = body.detail;
    } catch {
      // non-JSON error body — keep the status text
    }
    throw new Error(detail);
  }
  return response.json();
}

export async function apiGet(endpoint) {
  if (window.electronAPI?.apiGet) {
    return window.electronAPI.apiGet(endpoint);
  }
  return parseResponse(await fetch(`${API_BASE}${endpoint}`));
}

export async function apiPost(endpoint, data) {
  if (window.electronAPI?.apiPost) {
    return window.electronAPI.apiPost(endpoint, data);
  }
  const options = { method: 'POST' };
  if (data !== undefined) {
    options.headers = { 'Content-Type': 'application/json' };
    options.body = JSON.stringify(data);
  }
  return parseResponse(await fetch(`${API_BASE}${endpoint}`, options));
}

/** Build an absolute backend URL, e.g. for window.open() report exports. */
export function apiUrl(endpoint) {
  return `${API_BASE}${endpoint}`;
}
