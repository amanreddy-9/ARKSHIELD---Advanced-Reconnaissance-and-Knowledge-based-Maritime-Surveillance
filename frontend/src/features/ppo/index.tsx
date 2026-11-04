import { useEffect, useState } from 'react'
import {
  Cpu,
  Layers,
  RefreshCw,
  Shield,
} from 'lucide-react'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { getMissionHistory, getRLBenchmarks } from '@/api/analytics'
import { BenchmarkScenario, MissionHistoryEntry } from '@/api/types'
import { useSurveillanceStore } from '@/stores/surveillance-store'

export function PpoFeature() {
  const { droneResult } = useSurveillanceStore()

  const [benchmarks, setBenchmarks] = useState<Record<string, BenchmarkScenario>>({})
  const [history, setHistory] = useState<MissionHistoryEntry[]>([])
  const [loading, setLoading] = useState<boolean>(false)

  const fetchData = async () => {
    setLoading(true)
    try {
      const [bData, hData] = await Promise.all([getRLBenchmarks(), getMissionHistory()])
      setBenchmarks(bData)
      setHistory(hData)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const pModes = droneResult?.processing_mode_counts || {}
  const totalFrames = droneResult?.processed_frames || 1
  const lw = pModes.lightweight || 0
  const st = pModes.standard || 0
  const hv = pModes.heavy || 0
  const overrides = droneResult?.safety_overrides || 0
  const computeSaved = droneResult?.estimated_compute_reduction ?? 0

  return (
    <>
      <Header fixed>
        <div className='flex items-center gap-2'>
          <Cpu className='size-5 text-primary' />
          <div>
            <h1 className='text-sm font-bold tracking-normal font-sans text-foreground normal-case'>
              PPO Adaptive Edge Compute Analytics
            </h1>
            <p className='text-[10px] font-sans text-muted-foreground'>
              Gymnasium Surveillance Environment + Stable-Baselines3 PPO Policy & Safety Override
            </p>
          </div>
        </div>
        <div className='ms-auto flex items-center space-x-2'>
          <Search />
          <ThemeSwitch />
          <ProfileDropdown />
        </div>
      </Header>

      <Main className='space-y-4 p-4 md:p-6'>
        {/* Scientific Disclaimer Alert */}
        <div className='p-3.5 rounded-lg bg-secondary/30 border border-primary/20 text-xs font-sans text-muted-foreground leading-relaxed flex items-start gap-2.5'>
          <Shield className='size-4 text-primary shrink-0 mt-0.5' />
          <div>
            <span className='font-bold text-foreground'>Scientific & Operational Boundary: </span>
            Edge compute reductions model estimated resource conservation on the on-board GPU (bypassing full YOLO forward passes and heavy ConvNeXt crops during quiescent surveillance). This quantifies energy and computational savings on embedded platforms without claiming direct physical UAV battery hardware control.
          </div>
        </div>

        {/* Current Mission Telemetry */}
        {droneResult ? (
          <Card className='bg-card/90 border-border'>
            <CardHeader className='pb-3 border-b border-border/50 flex flex-row items-center justify-between'>
              <div>
                <CardTitle className='text-xs font-sans font-semibold tracking-normal normal-case text-foreground'>
                  Active Mission Adaptive Execution: {droneResult.scenario_name || 'Drone Video'}
                </CardTitle>
                <p className='text-[11px] text-muted-foreground font-sans'>
                  Mode: {droneResult.scan_mode || '15 FPS Fast Scan'} | Total Frames: {droneResult.processed_frames}
                </p>
              </div>
              <Badge variant='outline' className='font-sans text-xs text-primary border-primary/40'>
                {computeSaved.toFixed(1)}% COMPUTE REDUCTION
              </Badge>
            </CardHeader>
            <CardContent className='p-4 space-y-4'>
              <div className='grid grid-cols-2 sm:grid-cols-5 gap-3'>
                <div className='p-3 rounded-md bg-secondary/30 border border-border/60 font-sans'>
                  <span className='text-[10px] text-muted-foreground normal-case'>Total Frames</span>
                  <p className='text-lg font-bold text-foreground mt-1'>{droneResult.processed_frames}</p>
                  <p className='text-[10px] text-muted-foreground'>Analyzed</p>
                </div>

                <div className='p-3 rounded-md bg-primary/10 border border-primary/30 font-sans'>
                  <span className='text-[10px] text-primary normal-case'>LOW Mode (1/4 Freq)</span>
                  <p className='text-lg font-bold text-primary mt-1'>{lw}</p>
                  <p className='text-[10px] text-muted-foreground'>{((lw / totalFrames) * 100).toFixed(1)}% frames</p>
                </div>

                <div className='p-3 rounded-md bg-primary/10 border border-primary/30 font-sans'>
                  <span className='text-[10px] text-primary normal-case'>NORMAL Mode (1/2 Freq)</span>
                  <p className='text-lg font-bold text-primary mt-1'>{st}</p>
                  <p className='text-[10px] text-muted-foreground'>{((st / totalFrames) * 100).toFixed(1)}% frames</p>
                </div>

                <div className='p-3 rounded-md bg-primary/10 border border-primary/30 font-sans'>
                  <span className='text-[10px] text-primary normal-case'>HIGH Mode (Full Freq)</span>
                  <p className='text-lg font-bold text-primary mt-1'>{hv}</p>
                  <p className='text-[10px] text-muted-foreground'>{((hv / totalFrames) * 100).toFixed(1)}% frames</p>
                </div>

                <div className='p-3 rounded-md bg-amber-500/10 border border-amber-500/30 font-sans'>
                  <span className='text-[10px] text-amber-400 normal-case'>Safety Overrides</span>
                  <p className='text-lg font-bold text-amber-400 mt-1'>{overrides}</p>
                  <p className='text-[10px] text-muted-foreground'>Forced High Freq</p>
                </div>
              </div>

              {/* Progress Bar */}
              <div className='space-y-1.5 pt-1'>
                <div className='flex justify-between text-xs font-sans'>
                  <span className='text-muted-foreground'>Edge GPU Compute Conservation vs Exhaustive Scanning:</span>
                  <span className='text-primary font-bold'>{computeSaved.toFixed(1)}%</span>
                </div>
                <Progress value={computeSaved} className='h-2 bg-secondary' />
              </div>
            </CardContent>
          </Card>
        ) : (
          <Card className='bg-card/90 border-border p-6 text-center font-sans text-xs text-muted-foreground'>
            No drone sequence executed in active session. Execute a mission in Video tracking to inspect real-time frame throttling.
          </Card>
        )}

        {/* Multi-Scenario Benchmark Comparison Table */}
        <Card className='bg-card/90 border-border'>
          <CardHeader className='pb-3 border-b border-border/50 flex flex-row items-center justify-between'>
            <div>
              <CardTitle className='text-xs font-sans font-semibold tracking-normal normal-case text-foreground'>
                Multi-Scenario Benchmark: Exhaustive Baseline vs PPO Adaptive Policy
              </CardTitle>
              <p className='text-[11px] text-muted-foreground font-sans'>
                Quantitative metrics recorded on authentic full surveillance sequences
              </p>
            </div>
            <Button
              size='sm'
              variant='outline'
              onClick={fetchData}
              disabled={loading}
              className='font-sans text-xs border-primary/40 text-primary'
            >
              <RefreshCw className={`size-3.5 mr-1.5 ${loading ? 'animate-spin' : ''}`} /> Refresh Telemetry
            </Button>
          </CardHeader>
          <CardContent className='p-0 overflow-x-auto'>
            {Object.keys(benchmarks).length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow className='border-border/60 font-sans text-[11px] text-muted-foreground'>
                    <TableHead>Surveillance Scenario</TableHead>
                    <TableHead>Execution Mode</TableHead>
                    <TableHead>Total Frames</TableHead>
                    <TableHead>Full Compute (Baseline)</TableHead>
                    <TableHead>PPO Compute (Actual)</TableHead>
                    <TableHead>Estimated Compute Reduction</TableHead>
                    <TableHead>PPO Action Breakdown</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody className='font-sans text-xs'>
                  {Object.entries(benchmarks).map(([sceneName, sData]) => {
                    const fullCost = sData.full_processing?.estimated_compute_cost ?? sData.total_frames
                    const ppoCost = sData.ppo_adaptive_scheduler?.estimated_compute_cost ?? 0
                    const ppoRed = sData.ppo_adaptive_scheduler?.estimated_compute_reduction_pct ?? 0
                    const actions = sData.ppo_adaptive_scheduler?.action_distribution || {}
                    const scanMode = sData.scan_mode || '30 FPS Full Scan'

                    return (
                      <TableRow key={sceneName} className='border-border/40 hover:bg-muted/40'>
                        <TableCell className='font-semibold text-foreground'>{sceneName}</TableCell>
                        <TableCell className='text-muted-foreground'>{scanMode}</TableCell>
                        <TableCell className='text-muted-foreground'>{sData.total_frames}</TableCell>
                        <TableCell className='text-muted-foreground'>{fullCost.toFixed(1)} units</TableCell>
                        <TableCell className='font-bold text-primary'>{ppoCost.toFixed(1)} units</TableCell>
                        <TableCell>
                          <span
                            className={`px-1.5 py-0.5 rounded text-[11px] font-bold ${
                              ppoRed >= 50
                                ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                                : ppoRed >= 20
                                ? 'bg-red-500/15 text-primary border border-primary/30'
                                : 'bg-secondary text-muted-foreground'
                            }`}
                          >
                            {ppoRed.toFixed(2)}%
                          </span>
                        </TableCell>
                        <TableCell className='text-muted-foreground text-[11px]'>
                          LOW: {actions['0'] ?? 0} | NORM: {actions['1'] ?? 0} | HIGH: {actions['2'] ?? 0}
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            ) : (
              <div className='p-6 text-center font-sans text-xs text-muted-foreground'>
                No benchmark records found. Run a video sequence to populate the benchmark registry.
              </div>
            )}
          </CardContent>
        </Card>

        {/* Live Mission Execution History Log */}
        {history.length > 0 && (
          <Card className='bg-card/90 border-border'>
            <CardHeader className='pb-3 border-b border-border/50'>
              <CardTitle className='text-xs font-sans font-semibold tracking-normal normal-case text-foreground'>
                Live Mission Chronological Execution Registry ({history.length} Missions)
              </CardTitle>
              <p className='text-[11px] text-muted-foreground font-sans'>
                History of executed surveillance videos recording target classification and edge compute savings
              </p>
            </CardHeader>
            <CardContent className='p-0 overflow-x-auto'>
              <Table>
                <TableHeader>
                  <TableRow className='border-border/60 font-sans text-[11px] text-muted-foreground'>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>Surveillance Scenario</TableHead>
                    <TableHead>Execution Mode</TableHead>
                    <TableHead>Identified Class</TableHead>
                    <TableHead>Evidence Stability</TableHead>
                    <TableHead>Processed Frames</TableHead>
                    <TableHead>Compute Saved</TableHead>
                    <TableHead>Overrides</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody className='font-sans text-xs'>
                  {history.slice(-15).reverse().map((h, i) => (
                    <TableRow key={i} className='border-border/40 hover:bg-muted/40'>
                      <TableCell className='text-muted-foreground'>{h.timestamp}</TableCell>
                      <TableCell className='font-semibold text-foreground'>{h.scenario}</TableCell>
                      <TableCell className='text-muted-foreground'>{h.scan_mode}</TableCell>
                      <TableCell className='font-bold text-primary'>{h.vessel_class}</TableCell>
                      <TableCell className='text-muted-foreground'>{h.evidence_stability}</TableCell>
                      <TableCell className='text-muted-foreground'>{h.total_frames}</TableCell>
                      <TableCell className='font-bold text-emerald-400'>{h.compute_saved_pct}</TableCell>
                      <TableCell className='text-amber-400'>{h.safety_overrides}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}

        {/* PPO Architecture Specification Deep Dive */}
        <Card className='bg-card/90 border-border'>
          <CardHeader className='pb-2 border-b border-border/50'>
            <CardTitle className='text-xs font-sans font-semibold tracking-normal normal-case text-foreground flex items-center gap-2'>
              <Layers className='size-4 text-primary' />
              PPO Policy & Safety Override Architecture Specifications
            </CardTitle>
          </CardHeader>
          <CardContent className='p-4 font-sans text-xs space-y-3 text-muted-foreground'>
            <div>
              <span className='font-bold text-foreground'>8-Dimensional Normalized Observation Vector:</span>
              <ol className='list-decimal list-inside mt-1.5 space-y-1 pl-2 text-[11px]'>
                <li>Target visible indicator (`0.0` or `1.0`)</li>
                <li>Target center distance from frame centroid (normalized `[0.0, 1.0]`)</li>
                <li>Target relative bounding box area (`[0.0, 1.0]`)</li>
                <li>Frame scene complexity (`[0.0, 1.0]`)</li>
                <li>Total active tracks count (normalized `/ 10.0`)</li>
                <li>Target lost / occlusion persistence counter (normalized `/ 30.0`)</li>
                <li>Target velocity magnitude (normalized `/ 50.0`)</li>
                <li>Historical tracking stability score (`[0.0, 1.0]`)</li>
              </ol>
            </div>
            <div>
              <span className='font-bold text-foreground'>Discrete Action Space:</span>
              <ul className='list-disc list-inside mt-1.5 space-y-1 pl-2 text-[11px]'>
                <li><strong className='text-primary'>Action 0 (LOW)</strong>: Sample every 4th frame (cost 0.25). Quiescent open-sea surveillance.</li>
                <li><strong className='text-primary'>Action 1 (NORMAL)</strong>: Sample every 2nd frame (cost 0.50). Standard cruise cadence.</li>
                <li><strong className='text-primary'>Action 2 (HIGH)</strong>: Sample every frame (cost 1.00). High target density or sudden maneuvers.</li>
              </ul>
            </div>
            <div className='p-2.5 rounded bg-amber-500/10 border border-amber-500/20 text-amber-300 text-[11px]'>
              <span className='font-bold'>Hard Operational Safety Override Rule: </span>
              If target vessel is actively tracked but unobserved for ≥ 3 consecutive frames, or if &gt;3 adjacent vessels interact within collision proximity, the safety override automatically forces HIGH frequency processing regardless of the RL agent policy.
            </div>
          </CardContent>
        </Card>
      </Main>
    </>
  )
}
