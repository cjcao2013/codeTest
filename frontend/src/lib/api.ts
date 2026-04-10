import type { AssessConfig, MigrateConfig, RunRecord, RunDetail } from './types'

const BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? `HTTP ${res.status}`)
  }
  return res.json()
}

export async function startAssess(config: AssessConfig): Promise<{ run_id: string }> {
  return post('/api/assess', config)
}

export async function startMigrate(config: MigrateConfig): Promise<{ run_id: string }> {
  return post('/api/migrate', config)
}

export async function fetchHistory(): Promise<RunRecord[]> {
  const res = await fetch(`${BASE}/api/history`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export async function fetchRun(runId: string): Promise<RunDetail> {
  const res = await fetch(`${BASE}/api/history/${runId}`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export function createWs(path: string): WebSocket {
  const wsBase = BASE.replace(/^http/, 'ws')
  return new WebSocket(`${wsBase}${path}`)
}
