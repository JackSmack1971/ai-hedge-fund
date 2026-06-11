import { toast } from 'sonner';

export type RunKind = 'flow' | 'backtest';

interface HttpErrorMessages {
  authMessage: string;
  serverMessage: string;
  fallbackMessage: string;
}

function extractDetailFromPayload(payload: unknown): string {
  if (!payload || typeof payload !== 'object') {
    return '';
  }

  const record = payload as Record<string, unknown>;
  const detail = record.detail ?? record.message ?? record.error;

  if (typeof detail === 'string') {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail.map(item => (typeof item === 'string' ? item : JSON.stringify(item))).join(', ');
  }

  if (detail && typeof detail === 'object') {
    return JSON.stringify(detail);
  }

  return '';
}

export async function buildActionableHttpErrorMessage(response: Response, messages: HttpErrorMessages): Promise<string> {
  if (response.status === 401 || response.status === 403) {
    return messages.authMessage;
  }

  if (response.status >= 500) {
    return messages.serverMessage;
  }

  let detail = '';
  const contentType = response.headers.get('content-type') || '';

  if (contentType.includes('application/json')) {
    try {
      detail = extractDetailFromPayload(await response.clone().json());
    } catch {
      detail = '';
    }
  }

  if (!detail) {
    try {
      detail = (await response.clone().text()).trim();
    } catch {
      detail = '';
    }
  }

  if (detail) {
    return detail;
  }

  return `${messages.fallbackMessage} (${response.status})`;
}

export function buildActionableNetworkErrorMessage(error: unknown, fallbackMessage: string): string {
  const message = error instanceof Error ? error.message : String(error);

  if (/failed to fetch|networkerror|load failed/i.test(message)) {
    return fallbackMessage;
  }

  return message || fallbackMessage;
}

function getToastId(kind: RunKind, category: 'error' | 'warning' | 'cancelled', flowId: string | null): string {
  return `${kind}-run-${category}-${flowId ?? 'global'}`;
}

export function showRunErrorToast(kind: RunKind, flowId: string | null, message: string): void {
  toast.error(message, { id: getToastId(kind, 'error', flowId) });
}

export function showRunWarningToast(kind: RunKind, flowId: string | null, message: string): void {
  toast.warning(message, { id: getToastId(kind, 'warning', flowId) });
}

export function showRunCancelledToast(kind: RunKind, flowId: string | null): void {
  toast.info('Run cancelled', { id: getToastId(kind, 'cancelled', flowId) });
}
