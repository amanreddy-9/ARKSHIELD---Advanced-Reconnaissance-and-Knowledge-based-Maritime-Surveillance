import { apiClient } from './client'
import { SatelliteDetectionResponse, SatellitePreset } from './types'

export interface SatelliteDetectParams {
  file?: File | Blob
  weights?: string
  conf?: number
  iou?: number
}

export async function detectSatelliteImage(params: SatelliteDetectParams): Promise<SatelliteDetectionResponse> {
  const formData = new FormData()
  if (params.file) {
    formData.append('file', params.file)
  }
  if (params.weights) {
    formData.append('weights', params.weights)
  }
  if (params.conf !== undefined) {
    formData.append('conf', params.conf.toString())
  }
  if (params.iou !== undefined) {
    formData.append('iou', params.iou.toString())
  }

  const t0 = performance.now()
  const res = await apiClient.post<SatelliteDetectionResponse>('/satellite/detect', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 180000,
  })
  const processing_time_ms = Math.round(performance.now() - t0)
  return { ...res.data, processing_time_ms }
}

export async function getSatellitePresets(): Promise<SatellitePreset[]> {
  try {
    const res = await apiClient.get<{ presets: SatellitePreset[] }>('/satellite/presets', { timeout: 4000 })
    return res.data.presets || []
  } catch {
    return []
  }
}

export async function detectSatellitePreset(
  presetId: string,
  options?: { weights?: string; conf?: number; iou?: number }
): Promise<SatelliteDetectionResponse> {
  const t0 = performance.now()
  const res = await apiClient.post<SatelliteDetectionResponse>(
    '/satellite/detect-preset',
    {
      preset_id: presetId,
      weights: options?.weights,
      conf: options?.conf ?? 0.25,
      iou: options?.iou ?? 0.6,
    },
    { timeout: 180000 }
  )
  const processing_time_ms = Math.round(performance.now() - t0)
  return { ...res.data, processing_time_ms }
}
