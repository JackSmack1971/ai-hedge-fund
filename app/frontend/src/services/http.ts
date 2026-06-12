import { toast } from 'sonner';

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const BACKEND_API_TOKEN = import.meta.env.VITE_BACKEND_API_TOKEN?.trim() || '';

const AUTH_TOAST_IDS = {
  authFailed: 'backend-auth-failed',
  backendUnavailable: 'backend-unavailable',
} as const;

function buildHeaders(headers?: HeadersInit, contentType?: string): Headers {
  const merged = new Headers(headers ?? {});

  if (contentType && !merged.has('Content-Type')) {
    merged.set('Content-Type', contentType);
  }

  if (BACKEND_API_TOKEN) {
    merged.set('Authorization', `Bearer ${BACKEND_API_TOKEN}`);
  }

  return merged;
}

function showBackendAuthToast(status: number) {
  if (status === 503) {
    toast.error('Backend is not configured (missing BACKEND_API_TOKEN)', {
      id: AUTH_TOAST_IDS.backendUnavailable,
    });
    return;
  }

  toast.error('Backend authentication failed — check VITE_BACKEND_API_TOKEN', {
    id: AUTH_TOAST_IDS.authFailed,
  });
}

export function backendUrl(path: string): string {
  return `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;
}

export function backendJsonHeaders(headers?: HeadersInit): Headers {
  return buildHeaders(headers, 'application/json');
}

export async function backendFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const response = await fetch(backendUrl(path), {
    ...init,
    headers: buildHeaders(init.headers),
  });

  if (response.status === 401 || response.status === 403 || response.status === 503) {
    showBackendAuthToast(response.status);
  }

  return response;
}
