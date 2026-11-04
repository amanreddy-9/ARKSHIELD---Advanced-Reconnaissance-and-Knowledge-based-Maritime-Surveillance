import { create } from 'zustand'
import {
  ChatMessage,
  DroneVideoResponse,
  SatelliteDetectionResponse,
  SystemHealthResponse,
} from '@/api/types'

interface SurveillanceState {
  satelliteResult: SatelliteDetectionResponse | null
  setSatelliteResult: (res: SatelliteDetectionResponse | null) => void

  droneResult: DroneVideoResponse | null
  setDroneResult: (res: DroneVideoResponse | null) => void

  chatHistory: ChatMessage[]
  addChatMessage: (msg: ChatMessage) => void
  setChatHistory: (history: ChatMessage[]) => void
  clearChatHistory: () => void

  backendOnline: boolean
  pingMs: number
  systemHealth: SystemHealthResponse | null
  setSystemStatus: (online: boolean, ping: number, health?: SystemHealthResponse | null) => void
}

const DEFAULT_GREETING: ChatMessage = {
  role: 'assistant',
  content:
    'Tactical Maritime Surveillance Assistant online. Awaiting satellite optical imagery or drone tactical feeds for multi-vessel tracking, ConvNeXt-Tiny classification, and Groq Qwen-2.5 intelligence synthesis.',
}

export const useSurveillanceStore = create<SurveillanceState>((set) => ({
  satelliteResult: null,
  setSatelliteResult: (res) => set({ satelliteResult: res }),

  droneResult: null,
  setDroneResult: (res) => set({ droneResult: res }),

  chatHistory: [DEFAULT_GREETING],
  addChatMessage: (msg) => set((s) => ({ chatHistory: [...s.chatHistory, msg] })),
  setChatHistory: (history) => set({ chatHistory: history }),
  clearChatHistory: () => set({ chatHistory: [DEFAULT_GREETING] }),

  backendOnline: false,
  pingMs: 0,
  systemHealth: null,
  setSystemStatus: (online, ping, health = null) =>
    set({
      backendOnline: online,
      pingMs: ping,
      systemHealth: health,
    }),
}))
