import { useEffect } from 'react'
import { Activity, Cpu, Radio, Satellite, Server, Ship } from 'lucide-react'
import { checkBasicHealth } from '@/api/health'
import { useSurveillanceStore } from '@/stores/surveillance-store'

export function HudRibbon() {
  const { backendOnline, pingMs, setSystemStatus } = useSurveillanceStore()

  useEffect(() => {
    let isMounted = true
    const pollHealth = async () => {
      try {
        const res = await checkBasicHealth()
        if (isMounted) {
          setSystemStatus(true, res.ping_ms)
        }
      } catch {
        if (isMounted) {
          setSystemStatus(false, 0)
        }
      }
    }

    pollHealth()
    const timer = setInterval(pollHealth, 10000)
    return () => {
      isMounted = false
      clearInterval(timer)
    }
  }, [setSystemStatus])

  return (
    <div className='flex flex-wrap items-center gap-2 p-2.5 rounded-lg bg-card/80 border border-border text-xs font-sans shadow-sm backdrop-blur-sm'>
      {/* Backend Status */}
      <div
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md border ${
          backendOnline
            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
            : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
        }`}
      >
        <Server className='size-3.5' />
        <span>BACKEND: {backendOnline ? `ONLINE (${pingMs}ms)` : 'OFFLINE'}</span>
      </div>

      {/* High-Res Detector */}
      <div className='inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-primary/10 text-primary border border-primary/30'>
        <Satellite className='size-3.5' />
        <span>DETECTOR: YOLO11n-VHRV @ 1024px [mAP50: 94.6%]</span>
      </div>

      {/* Tracker */}
      <div className='inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-primary/10 text-primary border border-primary/30'>
        <Radio className='size-3.5' />
        <span>TRACKER: 8-State Kalman / 3-Stage Hungarian</span>
      </div>

      {/* PPO RL Scheduler */}
      <div className='inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-primary/10 text-primary border border-primary/30'>
        <Cpu className='size-3.5' />
        <span>RL: PPO-Clip + Safety Override</span>
      </div>

      {/* ConvNeXt-Tiny Classifier */}
      <div className='inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-primary/10 text-primary border border-primary/30'>
        <Ship className='size-3.5' />
        <span>CLASSIFIER: ConvNeXt-Tiny (10-Class)</span>
      </div>

      {/* Edge Compute Node */}
      <div className='inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-800 text-slate-300 border border-slate-700 ml-auto'>
        <Activity className='size-3.5 text-primary' />
        <span>NODE: RTX 3050 CUDA 12.6</span>
      </div>
    </div>
  )
}
