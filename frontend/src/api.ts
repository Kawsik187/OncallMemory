import type {
  IncidentInput,
  IncidentResponsePayload,
  ComparisonResponse,
  IncidentResolution,
  HealthStatus,
  PresetItem,
} from './types';

const API_BASE = '/api';

export async function fetchHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
  return res.json();
}

export async function fetchPresets(): Promise<PresetItem[]> {
  const res = await fetch(`${API_BASE}/presets`);
  if (!res.ok) throw new Error(`Failed to fetch presets: ${res.statusText}`);
  const data = await res.json();
  return data.presets || [];
}

export async function analyzeIncident(incident: IncidentInput): Promise<IncidentResponsePayload> {
  const res = await fetch(`${API_BASE}/incidents/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(incident),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Analysis request failed');
  }
  return res.json();
}

export async function compareIncident(incident: IncidentInput): Promise<ComparisonResponse> {
  const res = await fetch(`${API_BASE}/incidents/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(incident),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Comparison request failed');
  }
  return res.json();
}

export async function resolveIncident(resolution: IncidentResolution): Promise<{
  success: boolean;
  message: string;
  retained_content: string;
  bank_id: string;
}> {
  const res = await fetch(`${API_BASE}/incidents/resolve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(resolution),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Resolve request failed');
  }
  return res.json();
}

export async function seedBank(): Promise<{
  bank_id: string;
  total: number;
  retained: number;
  failed: number;
  details: any[];
}> {
  const res = await fetch(`${API_BASE}/seed`, {
    method: 'POST',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Seed request failed');
  }
  return res.json();
}

export async function reflectIncident(incident: IncidentInput): Promise<any> {
  const res = await fetch(`${API_BASE}/incidents/reflect`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(incident),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Reflection request failed');
  }
  return res.json();
}

