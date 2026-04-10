export interface RunRecord {
  run_id: string
  type: 'assess' | 'migrate'
  status: 'running' | 'success' | 'failed'
  started_at: string
  ended_at: string | null
  duration_seconds: number | null
}

export interface RunDetail extends RunRecord {
  report: string | null
}

export interface AssessConfig {
  project_dir: string
  report_out?: string
  volume_threshold?: string
}

export interface MigrateConfig {
  project_dir: string
  env?: string
  dry_run?: boolean
  report_out?: string
}

export type WsMessage =
  | { type: 'log'; line: string }
  | { type: 'done' }
  | { type: 'error'; message: string }
