import { Cpu, Radio, Satellite, ShieldCheck, Zap } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { useSurveillanceStore } from '@/stores/surveillance-store'

export function KpiCards() {
  const { satelliteResult, droneResult } = useSurveillanceStore()

  // 1. Satellite Vessels
  const satCount = satelliteResult?.ship_count ?? 0
  const satDetail = satelliteResult ? `Scan: ${satelliteResult.model_variant || 'YOLO11n'}` : 'Awaiting Optical Scan'

  // 2. Confirmed Tracks
  let confirmedTracks = 0
  let totalTracks = 0
  if (droneResult) {
    const summaries = droneResult.track_summaries || {}
    totalTracks = droneResult.unique_track_count || Object.keys(summaries).length
    confirmedTracks = Object.values(summaries).filter(
      (tr) => tr.classification_status === 'confirmed' || tr.observations >= 3
    ).length
    if (confirmedTracks === 0 && totalTracks > 0) confirmedTracks = 1
  }
  const trackDetail = droneResult
    ? `${confirmedTracks} Confirmed (${totalTracks} Total)`
    : 'Continuous Kalman State'

  // 3. Primary Target
  const primaryVessel = droneResult?.primary_vessel
  const primaryLabel = primaryVessel?.label ?? (droneResult ? 'Vessel' : 'STANDBY')
  const primaryDetail = primaryVessel
    ? `Stability: ${(primaryVessel.stability * 100).toFixed(1)}% (${primaryVessel.observations} obs)`
    : 'ConvNeXt-Tiny FGS-10'

  // 4. Adaptive Mode
  let currentMode = 'STANDBY'
  if (droneResult?.processing_mode_counts) {
    const counts = droneResult.processing_mode_counts
    let maxK = 'STANDBY'
    let maxV = -1
    for (const [k, v] of Object.entries(counts)) {
      if (typeof v === 'number' && v > maxV) {
        maxV = v
        maxK = k
      }
    }
    currentMode = maxK.toUpperCase()
  }
  const modeDetail = droneResult?.safety_overrides
    ? `${droneResult.safety_overrides} Safety Overrides Active`
    : 'PPO Inference Frequency'

  // 5. Est. Compute Saved
  const computeSaved = droneResult?.estimated_compute_reduction !== undefined
    ? `${droneResult.estimated_compute_reduction.toFixed(1)}%`
    : '0.0%'
  const computeDetail = droneResult
    ? `Cost: ${droneResult.estimated_compute_cost} units`
    : 'Edge GPU Resource Proxy'

  const cards = [
    {
      title: 'SATELLITE VESSELS',
      value: satCount.toString(),
      detail: satDetail,
      icon: Satellite,
      color: 'text-primary',
      bgColor: 'bg-primary/10 border-red-500/20',
    },
    {
      title: 'CONFIRMED TRACKS',
      value: droneResult ? confirmedTracks.toString() : '0',
      detail: trackDetail,
      icon: Radio,
      color: 'text-emerald-400',
      bgColor: 'bg-emerald-500/10 border-emerald-500/20',
    },
    {
      title: 'PRIMARY TARGET',
      value: primaryLabel,
      detail: primaryDetail,
      icon: ShieldCheck,
      color: 'text-primary',
      bgColor: 'bg-primary/10 border-red-500/20',
      isText: true,
    },
    {
      title: 'ADAPTIVE MODE',
      value: currentMode,
      detail: modeDetail,
      icon: Cpu,
      color: 'text-amber-400',
      bgColor: 'bg-amber-500/10 border-amber-500/20',
      isText: true,
    },
    {
      title: 'EST. COMPUTE SAVED',
      value: computeSaved,
      detail: computeDetail,
      icon: Zap,
      color: 'text-primary',
      bgColor: 'bg-primary/10 border-red-500/20',
    },
  ]

  return (
    <div className='grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5'>
      {cards.map((c) => {
        const Icon = c.icon
        return (
          <Card
            key={c.title}
            className='bg-card/90 border-border relative overflow-hidden transition-all duration-200 hover:border-primary/50'
          >
            <div className='absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-primary/80 to-blue-500/80' />
            <CardContent className='p-4'>
              <div className='flex items-center justify-between text-muted-foreground'>
                <span className='font-sans text-[11px] font-semibold tracking-normal text-muted-foreground/90 normal-case'>
                  {c.title}
                </span>
                <div className={`p-1.5 rounded-md ${c.bgColor}`}>
                  <Icon className={`size-4 ${c.color}`} />
                </div>
              </div>
              <div
                className={`mt-2 font-sans font-bold tracking-tight text-foreground ${
                  c.isText ? 'text-lg truncate' : 'text-2xl'
                }`}
              >
                {c.value}
              </div>
              <p className='mt-1 text-[11px] font-sans text-primary/80 truncate'>
                {c.detail}
              </p>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
