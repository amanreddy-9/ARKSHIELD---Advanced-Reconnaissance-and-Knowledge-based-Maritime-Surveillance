import { apiClient } from './client'
import {
  BenchmarkScenario,
  DiagnosticSample,
  DiagnosticsMetricsData,
  MissionHistoryEntry,
} from './types'

export async function getRLBenchmarks(): Promise<Record<string, BenchmarkScenario>> {
  try {
    const res = await apiClient.get<Record<string, BenchmarkScenario>>('/rl/benchmarks', { timeout: 4000 })
    return res.data || {}
  } catch {
    return {}
  }
}

export async function getMissionHistory(): Promise<MissionHistoryEntry[]> {
  try {
    const res = await apiClient.get<MissionHistoryEntry[]>('/rl/history', { timeout: 4000 })
    return res.data || []
  } catch {
    return []
  }
}

export async function getDiagnosticsMetrics(): Promise<DiagnosticsMetricsData> {
  try {
    const res = await apiClient.get<DiagnosticsMetricsData>('/diagnostics/metrics', { timeout: 4000 })
    return res.data || {}
  } catch {
    return {}
  }
}

export async function getDiagnosticsSamples(): Promise<DiagnosticSample[]> {
  try {
    const res = await apiClient.get<{ samples: DiagnosticSample[] }>('/diagnostics/samples', { timeout: 4000 })
    return res.data.samples || []
  } catch {
    return []
  }
}
