import { ComparisonResult, HealthInfo, HistoryItem, VerificationResponse } from '../types';

const API_BASE = '';

export async function fetchHealth(): Promise<HealthInfo> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) {
    throw new Error(`Health check failed with HTTP ${res.status}`);
  }
  return res.json();
}

export async function verifyAnswer(
  answerText: string,
  question?: string,
  mode: 'QUICK_CHECK' | 'DEEP_CHECK' = 'DEEP_CHECK',
  signal?: AbortSignal
): Promise<VerificationResponse> {
  const res = await fetch(`${API_BASE}/api/v1/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      answer_text: answerText,
      question: question || null,
      mode,
    }),
    signal,
  });

  const data = await res.json();

  if (!res.ok) {
    const errorDetail = data.detail || {};
    const message = errorDetail.message || data.message || `Verification failed with HTTP ${res.status}`;
    const err = new Error(message);
    (err as any).errorType = errorDetail.error;
    (err as any).details = errorDetail.details;
    (err as any).status = res.status;
    throw err;
  }

  return data;
}

export async function fetchHistory(): Promise<HistoryItem[]> {
  const res = await fetch(`${API_BASE}/api/v1/history`);
  if (!res.ok) {
    throw new Error(`Failed to load history: HTTP ${res.status}`);
  }
  return res.json();
}

export async function fetchRunDetails(runId: string): Promise<VerificationResponse> {
  const res = await fetch(`${API_BASE}/api/v1/history/${runId}`);
  if (!res.ok) {
    throw new Error(`Failed to load run ${runId}: HTTP ${res.status}`);
  }
  return res.json();
}

export async function deleteRun(runId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/history/${runId}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    throw new Error(`Failed to delete run ${runId}`);
  }
}

export async function compareRuns(runA: string, runB: string): Promise<ComparisonResult> {
  const res = await fetch(`${API_BASE}/api/v1/history/compare?run_a=${encodeURIComponent(runA)}&run_b=${encodeURIComponent(runB)}`);
  if (!res.ok) {
    throw new Error(`Comparison failed with HTTP ${res.status}`);
  }
  return res.json();
}

export function exportRunJsonUrl(runId: string): string {
  return `${API_BASE}/api/v1/history/${runId}/export`;
}
