import { Gauge } from 'lucide-react'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

const DETECTOR_PERF = [
  { model: 'YOLO11n Baseline @ 640px', res: '640 × 640', latency: '6.71 ms', fps: '149.0 FPS', vram: '1.2 GB', mAP50: '87.29%' },
  { model: 'YOLO11n Baseline @ 1024px', res: '1024 × 1024', latency: '16.24 ms', fps: '61.58 FPS', vram: '2.1 GB', mAP50: '94.63%' },
  { model: '🏆 YOLO11n Custom @ 1024px', res: '1024 × 1024', latency: '15.80 ms', fps: '63.29 FPS', vram: '2.1 GB', mAP50: '96.84%' },
]

const RL_COMPUTE_SAVINGS = [
  { scenario: 'Empty Sea Surveillance', frames: 300, baseline: '300.0 units', ppo: '75.0 units', saved: '75.00%', state: '100% LOW Mode' },
  { scenario: 'Cruise Ship Mission', frames: 577, baseline: '577.0 units', ppo: '276.2 units', saved: '52.12%', state: 'Intermittent Cruise' },
  { scenario: 'Oil Tanker Mission', frames: 655, baseline: '655.0 units', ppo: '357.2 units', saved: '45.46%', state: 'Tactical Maneuver' },
  { scenario: 'Frigate Long-Range Patrol', frames: 360, baseline: '360.0 units', ppo: '259.2 units', saved: '28.00%', state: 'Patrol / Scan' },
]

export function PerformanceFeature() {
  return (
    <>
      <Header fixed>
        <div className='flex items-center gap-2'>
          <Gauge className='size-5 text-primary' />
          <div>
            <h1 className='text-sm font-bold tracking-normal font-sans text-foreground normal-case'>
              System Performance & Latency Telemetry
            </h1>
            <p className='text-[10px] font-sans text-muted-foreground'>
              Benchmarked on NVIDIA RTX 3050 Laptop GPU (4096 MiB VRAM, CUDA 12.6, PyTorch 2.14)
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
        {/* KPI Row */}
        <div className='grid grid-cols-1 sm:grid-cols-4 gap-3'>
          <Card className='bg-card border-border p-3.5'>
            <span className='font-sans text-[10px] text-muted-foreground normal-case'>Detector Throughput</span>
            <p className='font-sans text-2xl font-bold text-primary mt-1'>63.3 FPS</p>
            <p className='font-sans text-[10px] text-muted-foreground mt-0.5'>YOLO11n-VHRV @ 1024px</p>
          </Card>

          <Card className='bg-card border-border p-3.5'>
            <span className='font-sans text-[10px] text-muted-foreground normal-case'>Inference Latency</span>
            <p className='font-sans text-2xl font-bold text-emerald-400 mt-1'>15.8 ms</p>
            <p className='font-sans text-[10px] text-muted-foreground mt-0.5'>Real-Time Edge Capable</p>
          </Card>

          <Card className='bg-card border-border p-3.5'>
            <span className='font-sans text-[10px] text-muted-foreground normal-case'>Max Compute Saved</span>
            <p className='font-sans text-2xl font-bold text-amber-400 mt-1'>75.0%</p>
            <p className='font-sans text-[10px] text-muted-foreground mt-0.5'>Empty Sea Surveillance</p>
          </Card>

          <Card className='bg-card border-border p-3.5'>
            <span className='font-sans text-[10px] text-muted-foreground normal-case'>Classifier Latency</span>
            <p className='font-sans text-2xl font-bold text-primary mt-1'>4.2 ms</p>
            <p className='font-sans text-[10px] text-muted-foreground mt-0.5'>ConvNeXt-Tiny Crop</p>
          </Card>
        </div>

        {/* High-Resolution Detection Performance Benchmark */}
        <Card className='bg-card/90 border-border'>
          <CardHeader className='pb-3 border-b border-border/50 flex flex-row items-center justify-between'>
            <div>
              <CardTitle className='text-xs font-sans font-semibold tracking-normal normal-case text-foreground'>
                Detection Latency, Throughput & Resolution Trade-Off
              </CardTitle>
              <p className='text-[11px] text-muted-foreground font-sans'>
                Quantitative evaluation on independent VHRV test split (150 images, 1,191 vessels)
              </p>
            </div>
            <Badge variant='outline' className='font-sans text-xs text-primary border-primary/40'>
              CUDA 12.6 BENCHMARK
            </Badge>
          </CardHeader>
          <CardContent className='p-0 overflow-x-auto'>
            <Table>
              <TableHeader>
                <TableRow className='border-border/60 font-sans text-[11px] text-muted-foreground'>
                  <TableHead>Model Configuration</TableHead>
                  <TableHead>Resolution</TableHead>
                  <TableHead>Inference Latency</TableHead>
                  <TableHead>Throughput (FPS)</TableHead>
                  <TableHead>VRAM Footprint</TableHead>
                  <TableHead>Accuracy (mAP@50)</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody className='font-sans text-xs'>
                {DETECTOR_PERF.map((m, idx) => (
                  <TableRow key={idx} className='border-border/40 hover:bg-muted/40'>
                    <TableCell className='font-bold text-foreground'>{m.model}</TableCell>
                    <TableCell className='text-muted-foreground'>{m.res}</TableCell>
                    <TableCell className='font-bold text-emerald-400'>{m.latency}</TableCell>
                    <TableCell className='text-primary'>{m.fps}</TableCell>
                    <TableCell className='text-muted-foreground'>{m.vram}</TableCell>
                    <TableCell className='font-bold text-primary'>{m.mAP50}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* RL Compute Conservation Benchmarks */}
        <Card className='bg-card/90 border-border'>
          <CardHeader className='pb-3 border-b border-border/50'>
            <CardTitle className='text-xs font-sans font-semibold tracking-normal normal-case text-foreground'>
              PPO Dynamic Edge-Compute Conservation Across Scenarios
            </CardTitle>
            <p className='text-[11px] text-muted-foreground font-sans'>
              Estimated GPU energy proxy reduction relative to full-frame exhaustive scanning
            </p>
          </CardHeader>
          <CardContent className='p-0 overflow-x-auto'>
            <Table>
              <TableHeader>
                <TableRow className='border-border/60 font-sans text-[11px] text-muted-foreground'>
                  <TableHead>Surveillance Scenario</TableHead>
                  <TableHead>Frames</TableHead>
                  <TableHead>Full Compute Baseline</TableHead>
                  <TableHead>PPO Adaptive Compute</TableHead>
                  <TableHead>Resource Reduction</TableHead>
                  <TableHead>Primary Operating State</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody className='font-sans text-xs'>
                {RL_COMPUTE_SAVINGS.map((s, idx) => (
                  <TableRow key={idx} className='border-border/40 hover:bg-muted/40'>
                    <TableCell className='font-bold text-foreground'>{s.scenario}</TableCell>
                    <TableCell className='text-muted-foreground'>{s.frames}</TableCell>
                    <TableCell className='text-muted-foreground'>{s.baseline}</TableCell>
                    <TableCell className='font-bold text-primary'>{s.ppo}</TableCell>
                    <TableCell className='font-bold text-emerald-400'>{s.saved}</TableCell>
                    <TableCell className='text-muted-foreground'>{s.state}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </Main>
    </>
  )
}
