import { apiClient } from './client'
import { DronePreset, DroneVideoResponse } from './types'

export interface DroneVideoParams {
  file?: File | Blob
  target_x?: number
  target_y?: number
  sample_every?: number
}

export async function processDroneVideo(params: DroneVideoParams): Promise<DroneVideoResponse> {
  const formData = new FormData()
  if (params.file) {
    formData.append('file', params.file)
  }
  formData.append('target_x', (params.target_x ?? 0).toString())
  formData.append('target_y', (params.target_y ?? 0).toString())
  formData.append('sample_every', (params.sample_every ?? 2).toString())

  const res = await apiClient.post<DroneVideoResponse>('/drone/video', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 600000, // 10 min for full video
  })
  return res.data
}

export async function getDronePresets(): Promise<DronePreset[]> {
  try {
    const res = await apiClient.get<{ presets: DronePreset[] }>('/drone/presets', { timeout: 4000 })
    return res.data.presets || []
  } catch {
    return []
  }
}

export async function processDronePresetVideo(
  presetId: string,
  options?: { target_x?: number; target_y?: number; sample_every?: number; max_frames?: number | null }
): Promise<DroneVideoResponse> {
  const res = await apiClient.post<DroneVideoResponse>(
    '/drone/preset-video',
    {
      preset_id: presetId,
      target_x: options?.target_x ?? 0,
      target_y: options?.target_y ?? 0,
      sample_every: options?.sample_every ?? 2,
      max_frames: options?.max_frames ?? null,
    },
    { timeout: 600000 }
  )
  return res.data
}
