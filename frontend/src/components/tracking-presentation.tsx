import { useSurveillanceStore } from '@/stores/surveillance-store'

export function TrackingPresentation() {
  const result = useSurveillanceStore((s) => s.droneResult)
  const frames = result?.frames ?? []
  const latest = [...frames].reverse().find((frame) => frame.tracking_diagnostics)
  const diagnostics = latest?.tracking_diagnostics
  const matches = frames.reduce((total, frame) => {
    frame.tracking_diagnostics?.stage_matches.forEach((count, i) => { total[i] += count })
    return total
  }, [0, 0, 0])

  return (
    <section className='rounded-xl border border-border bg-card p-4' aria-label='Tracking method'>
      <div className='flex flex-wrap items-center justify-between gap-2'>
        <h2 className='text-sm font-semibold'>How vessel tracking works</h2>
        <span className='rounded-full bg-primary/10 px-2.5 py-1 text-xs text-primary'>8-state Kalman filter</span>
      </div>
      <p className='mt-2 text-sm leading-relaxed text-muted-foreground'>The filter predicts each vessel’s position and size, then corrects the prediction when a new detection arrives.</p>
      <p className='mt-1 text-xs text-muted-foreground'>Eight values: horizontal and vertical position, width and height, plus the rate of change of each.</p>
      <div className='mt-4 grid gap-3 sm:grid-cols-3'>
        {[
          ['1. Match clear detections', 'Connect confident detections to existing vessels.'],
          ['2. Recover weak detections', 'Use lower-confidence detections for unmatched vessels.'],
          ['3. Find returning vessels', 'Reconnect vessels after they briefly disappear.'],
        ].map(([title, explanation], i) => (
          <div key={title} className='rounded-lg border border-border bg-muted/30 p-3'>
            <h3 className='text-sm font-medium'>{title}</h3>
            <p className='mt-1 text-xs leading-relaxed text-muted-foreground'>{explanation}</p>
            {diagnostics && <p className='mt-2 text-xs text-primary'>{matches[i]} matches in this video</p>}
          </div>
        ))}
      </div>
      <p className='mt-3 text-xs text-muted-foreground'>Three-stage Hungarian association assigns each detection to at most one vessel.{!diagnostics && ' Run a video to see match counts.'}</p>
    </section>
  )
}
