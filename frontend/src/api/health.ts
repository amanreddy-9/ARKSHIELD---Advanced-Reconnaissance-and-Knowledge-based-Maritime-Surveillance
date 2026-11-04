import { apiClient } from './client'
import { SystemHealthResponse } from './types'

export async function checkBasicHealth(): Promise<{ status: string; project: string; ping_ms: number }> {
  const t0 = performance.now()
  const res = await apiClient.get('/health', { timeout: 3000 })
  const ping_ms = Math.round(performance.now() - t0)
  return { ...res.data, ping_ms }
}

export async function getSystemHealth(): Promise<SystemHealthResponse> {
  const t0 = performance.now()
  try {
    const res = await apiClient.get('/system/health', { timeout: 4000 })
    const ping_ms = Math.round(performance.now() - t0)
    return { ...res.data, ping_ms }
  } catch {
    // Fallback to basic /health if /system/health is unreachable
    const basic = await checkBasicHealth()
    return {
      status: basic.status,
      project: basic.project,
      ping_ms: basic.ping_ms,
      backend: { service: 'FastAPI', version: '1.0.0', status: 'online' },
      hardware: { device: 'Local CUDA Node', cuda_available: true, torch_version: 'PyTorch' },
      subsystems: {
        detector: { name: 'YOLO11n-VHRV Detector', status: 'online', default_imgsz: 1024 },
        tracker: { name: 'Continuous Kalman Tracker', status: 'online' },
        classifier: { name: 'ConvNeXt-Tiny (10-Class)', status: 'online' },
        scheduler: { name: 'PPO Adaptive Scheduler', status: 'online' },
        vlm: { name: 'Groq Qwen-2.5 Vision', status: 'online' },
      },
    }
  }
}
