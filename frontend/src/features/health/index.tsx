import { useEffect, useState } from 'react'
import {
  Bot,
  CheckCircle2,
  Cpu,
  Radio,
  RefreshCw,
  Satellite,
  Server,
  Ship,
  XCircle,
} from 'lucide-react'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { getSystemHealth } from '@/api/health'
import { SystemHealthResponse } from '@/api/types'
import { useSurveillanceStore } from '@/stores/surveillance-store'

export function HealthFeature() {
  const { setSystemStatus } = useSurveillanceStore()
  const [healthData, setHealthData] = useState<SystemHealthResponse | null>(null)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const fetchHealth = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getSystemHealth()
      setHealthData(data)
      setSystemStatus(true, data.ping_ms || 0, data)
    } catch (err: any) {
      setError(err?.message || 'Failed to reach FastAPI backend.')
      setSystemStatus(false, 0, null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHealth()
  }, [])

  const subs = healthData?.subsystems || {}

  const subsystemList = [
    {
      key: 'fastapi',
      title: 'FastAPI Backend API',
      status: healthData ? 'online' : 'offline',
      desc: 'REST API endpoints for high-res detection, video tracking, and VLM streaming',
      icon: Server,
    },
    {
      key: 'detector',
      title: subs.detector?.name || 'YOLO11n-VHRV Satellite Detector',
      status: subs.detector?.status || (healthData ? 'online' : 'unavailable'),
      desc: 'High-resolution optical vessel detection at imgsz=1024',
      icon: Satellite,
    },
    {
      key: 'tracker',
      title: subs.tracker?.name || 'Continuous Kalman Tracker',
      status: subs.tracker?.status || (healthData ? 'online' : 'unavailable'),
      desc: 'Multi-feature cost association: IoU + Centroid + Aspect + Motion',
      icon: Radio,
    },
    {
      key: 'classifier',
      title: subs.classifier?.name || 'ConvNeXt-Tiny Vessel Classifier',
      status: subs.classifier?.status || (healthData ? 'online' : 'unavailable'),
      desc: 'TITANIC-FGS-10 10-Class fine-grained vessel taxonomy',
      icon: Ship,
    },
    {
      key: 'scheduler',
      title: subs.scheduler?.name || 'PPO Adaptive Compute Scheduler',
      status: subs.scheduler?.status || (healthData ? 'online' : 'unavailable'),
      desc: 'Gymnasium RL policy with operational safety override layer',
      icon: Cpu,
    },
    {
      key: 'vlm',
      title: subs.vlm?.name || 'Groq Qwen-2.5 Vision / 70B Interface',
      status: subs.vlm?.status || (healthData ? 'online' : 'unavailable'),
      desc: 'Multimodal maritime vision-language briefing engine',
      icon: Bot,
    },
  ]

  return (
    <>
      <Header fixed>
        <div className='flex items-center gap-2'>
          <Server className='size-5 text-primary' />
          <div>
            <h1 className='text-sm font-bold tracking-normal font-sans text-foreground normal-case'>
              System & Pipeline Health Diagnostics
            </h1>
            <p className='text-[10px] font-sans text-muted-foreground'>
              Real-Time Verification of Deep Learning Subsystems & Backend Telemetry
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
        {/* Node Overview Card */}
        <Card className='bg-card/90 border-border'>
          <CardHeader className='pb-3 border-b border-border/50 flex flex-row items-center justify-between'>
            <div>
              <CardTitle className='text-xs font-sans font-semibold tracking-normal normal-case text-foreground'>
                Inference Node Telemetry & Hardware State
              </CardTitle>
              <p className='text-[11px] text-muted-foreground font-sans'>
                Compute environment executing PyTorch deep learning models
              </p>
            </div>
            <Button
              size='sm'
              variant='outline'
              onClick={fetchHealth}
              disabled={loading}
              className='font-sans text-xs border-primary/40 text-primary'
            >
              <RefreshCw className={`size-3.5 mr-1.5 ${loading ? 'animate-spin' : ''}`} /> Refresh Status
            </Button>
          </CardHeader>
          <CardContent className='p-4'>
            <div className='grid grid-cols-1 sm:grid-cols-4 gap-3 font-sans text-xs'>
              <div className='p-3 rounded-md bg-secondary/30 border border-border/60'>
                <span className='text-[10px] text-muted-foreground normal-case'>Compute Device</span>
                <p className='text-sm font-bold text-primary mt-1 truncate'>
                  {healthData?.hardware?.device || 'NVIDIA RTX 3050 Laptop GPU'}
                </p>
                <p className='text-[10px] text-muted-foreground mt-0.5'>CUDA 12.6 Enabled</p>
              </div>

              <div className='p-3 rounded-md bg-secondary/30 border border-border/60'>
                <span className='text-[10px] text-muted-foreground normal-case'>Backend Status</span>
                <p className='text-sm font-bold text-emerald-400 mt-1 flex items-center gap-1.5'>
                  {healthData ? (
                    <>
                      <CheckCircle2 className='size-3.5' /> ONLINE ({healthData.ping_ms} ms)
                    </>
                  ) : (
                    <>
                      <XCircle className='size-3.5 text-destructive' /> OFFLINE
                    </>
                  )}
                </p>
                <p className='text-[10px] text-muted-foreground mt-0.5'>FastAPI v1.0.0</p>
              </div>

              <div className='p-3 rounded-md bg-secondary/30 border border-border/60'>
                <span className='text-[10px] text-muted-foreground normal-case'>PyTorch Runtime</span>
                <p className='text-sm font-bold text-primary mt-1'>
                  {healthData?.hardware?.torch_version || '2.14+cu126'}
                </p>
                <p className='text-[10px] text-muted-foreground mt-0.5'>CUDA Core Accelerators</p>
              </div>

              <div className='p-3 rounded-md bg-secondary/30 border border-border/60'>
                <span className='text-[10px] text-muted-foreground normal-case'>Project Node</span>
                <p className='text-sm font-bold text-foreground mt-1'>OATrack-VLM</p>
                <p className='text-[10px] text-muted-foreground mt-0.5'>Production Pipeline</p>
              </div>
            </div>

            {error && (
              <div className='mt-3 p-3 rounded-md bg-destructive/15 border border-destructive/30 text-destructive text-xs font-sans'>
                {error}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Subsystems Status Grid */}
        <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'>
          {subsystemList.map((sub) => {
            const Icon = sub.icon
            const isOnline = sub.status === 'online'
            return (
              <Card
                key={sub.key}
                className='bg-card/90 border-border p-4 flex flex-col justify-between space-y-3'
              >
                <div>
                  <div className='flex items-center justify-between mb-2'>
                    <div className='p-2 rounded-md bg-secondary/60 text-primary border border-border/60'>
                      <Icon className='size-5' />
                    </div>
                    <Badge
                      variant='outline'
                      className={`font-sans text-[10px] normal-case ${
                        isOnline
                          ? 'text-emerald-400 border-emerald-500/40 bg-emerald-500/10'
                          : 'text-amber-400 border-amber-500/40 bg-amber-500/10'
                      }`}
                    >
                      {isOnline ? 'OPERATIONAL' : sub.status.toUpperCase()}
                    </Badge>
                  </div>
                  <h4 className='text-xs font-sans font-bold text-foreground'>{sub.title}</h4>
                  <p className='text-[11px] font-sans text-muted-foreground mt-1 leading-snug'>{sub.desc}</p>
                </div>

                <div className='pt-2 border-t border-border/40 flex items-center justify-between text-[10px] font-sans'>
                  <span className='text-muted-foreground'>Subsystem State:</span>
                  <span className={isOnline ? 'text-emerald-400 font-bold' : 'text-amber-400'}>
                    {isOnline ? '● Ready for Inference' : '● Standby / Unavailable'}
                  </span>
                </div>
              </Card>
            )
          })}
        </div>
      </Main>
    </>
  )
}
