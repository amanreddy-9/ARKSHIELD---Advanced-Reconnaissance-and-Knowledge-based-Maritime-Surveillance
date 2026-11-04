import { Link } from '@tanstack/react-router'
import {
  ArrowRight,
  Bot,
  Compass,
  Play,
  Radio,
  Satellite,
} from 'lucide-react'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useSurveillanceStore } from '@/stores/surveillance-store'
import { resolveBackendUrl } from '@/api/client'
import { KpiCards } from './components/kpi-cards'

export function Dashboard() {
  const { satelliteResult, droneResult } = useSurveillanceStore()

  const rawSatUrl = satelliteResult?.raw_image_url
    ? resolveBackendUrl(satelliteResult.raw_image_url)
    : null
  const annotSatUrl = satelliteResult?.annotated_image_url
    ? resolveBackendUrl(satelliteResult.annotated_image_url)
    : null

  const annotVideoUrl = droneResult?.annotated_video_url
    ? resolveBackendUrl(droneResult.annotated_video_url)
    : null

  const vlmText = typeof satelliteResult?.vlm_analysis === 'string'
    ? satelliteResult.vlm_analysis
    : (satelliteResult?.vlm_analysis as any)?.text || (satelliteResult?.vlm_analysis as any)?.briefing || null

  return (
    <>
      {/* Top Command Bar */}
      <Header fixed>
        <div className='flex items-center gap-3'>
          <Compass className='size-5 text-primary animate-pulse' />
          <div>
            <h1 className='text-sm font-bold tracking-normal font-sans text-foreground normal-case'>
              Maritime surveillance
            </h1>
            <p className='text-[10px] font-sans text-muted-foreground hidden sm:block'>
              Vessel detection and tracking
            </p>
          </div>
        </div>
        <div className='ms-auto flex items-center space-x-2'>
          <Search />
          <ThemeSwitch />
          <ProfileDropdown />
        </div>
      </Header>

      <Main className='maritime-workspace space-y-4 p-4 md:p-6'>
        {/* HUD Ribbon Bar */}
        <p className='text-sm text-muted-foreground'>Analyze satellite images, track vessels in video, and review your results.</p>

        {/* 5 KPI Metric Cards */}
        <KpiCards />

        {/* 6-Stage Autonomous Pipeline Architecture Flow */}


        {/* Mission Workstations Quick Status */}
        <div className='grid grid-cols-1 lg:grid-cols-2 gap-4'>
          {/* SATELLITE DETECTION QUICK STATUS */}
          <Card className='bg-card/90 border-border'>
            <CardHeader className='pb-3 border-b border-border/50 flex flex-row items-center justify-between'>
              <div className='flex items-center gap-2'>
                <div className='p-1.5 rounded-md bg-primary/10 text-primary border border-primary/30'>
                  <Satellite className='size-4' />
                </div>
                <div>
                  <CardTitle className='text-sm font-sans font-semibold'>
                    Satellite images
                  </CardTitle>
                  <p className='text-[11px] text-muted-foreground'>
                    High-Res Optical Scanner (1024×1024 px)
                  </p>
                </div>
              </div>
              <Button asChild size='sm' variant='outline' className='font-sans text-xs border-primary/40 text-primary'>
                <Link to='/satellite'>
                  Workstation <ArrowRight className='size-3 ml-1' />
                </Link>
              </Button>
            </CardHeader>
            <CardContent className='p-4 space-y-3'>
              {satelliteResult ? (
                <div className='space-y-3'>
                  <div className='flex items-center justify-between font-sans text-xs'>
                    <span className='text-muted-foreground'>Detected Ships:</span>
                    <span className='font-bold text-primary'>{satelliteResult.ship_count} Vessels</span>
                  </div>
                  <div className='flex items-center justify-between font-sans text-xs'>
                    <span className='text-muted-foreground'>Detector Model:</span>
                    <span className='text-foreground'>{satelliteResult.model_variant || 'YOLO11n-VHRV'}</span>
                  </div>
                  <div className='flex items-center justify-between font-sans text-xs'>
                    <span className='text-muted-foreground'>Confidence / IoU:</span>
                    <span className='text-foreground'>
                      {satelliteResult.conf_threshold?.toFixed(2) || '0.25'} / {satelliteResult.iou_threshold?.toFixed(2) || '0.60'}
                    </span>
                  </div>

                  {/* Thumbnail Preview */}
                  <div className='grid grid-cols-2 gap-2 pt-1'>
                    <div className='rounded-md overflow-hidden border border-border bg-black/40 h-32 flex items-center justify-center text-xs text-muted-foreground'>
                      {rawSatUrl ? (
                        <img src={rawSatUrl} alt='Raw Feed' className='w-full h-full object-cover' />
                      ) : (
                        <span>Raw Optical Feed</span>
                      )}
                    </div>
                    <div className='rounded-md overflow-hidden border border-border bg-black/40 h-32 flex items-center justify-center text-xs text-muted-foreground'>
                      {annotSatUrl ? (
                        <img src={annotSatUrl} alt='Annotated Overlay' className='w-full h-full object-cover' />
                      ) : (
                        <span>Annotated Bounding Boxes</span>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className='py-8 text-center text-muted-foreground font-sans space-y-3'>
                  <Satellite className='size-10 mx-auto text-muted-foreground/40' />
                  <p className='text-xs'>No satellite image analyzed in current session.</p>
                  <Button asChild size='sm' className='font-sans text-xs bg-primary text-primary-foreground hover:bg-primary/90'>
                    <Link to='/satellite'>
                      <Play className='size-3 mr-1.5' /> Analyze image
                    </Link>
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* UAV TRACKING QUICK STATUS */}
          <Card className='bg-card/90 border-border'>
            <CardHeader className='pb-3 border-b border-border/50 flex flex-row items-center justify-between'>
              <div className='flex items-center gap-2'>
                <div className='p-1.5 rounded-md bg-primary/10 text-primary border border-primary/30'>
                  <Radio className='size-4' />
                </div>
                <div>
                  <CardTitle className='text-sm font-sans font-semibold'>
                    Vessel video
                  </CardTitle>
                  <p className='text-[11px] text-muted-foreground'>
                    Continuous Multi-Feature Kalman Tracking
                  </p>
                </div>
              </div>
              <Button asChild size='sm' variant='outline' className='font-sans text-xs border-primary/40 text-primary'>
                <Link to='/tracking'>
                  Workstation <ArrowRight className='size-3 ml-1' />
                </Link>
              </Button>
            </CardHeader>
            <CardContent className='p-4 space-y-3'>
              {droneResult ? (
                <div className='space-y-3'>
                  <div className='flex items-center justify-between font-sans text-xs'>
                    <span className='text-muted-foreground'>Primary Target:</span>
                    <span className='font-bold text-emerald-400'>
                      {droneResult.primary_vessel?.label || 'Vessel'} (ID #{droneResult.primary_vessel?.track_id || 1})
                    </span>
                  </div>
                  <div className='flex items-center justify-between font-sans text-xs'>
                    <span className='text-muted-foreground'>Processed Frames:</span>
                    <span className='text-foreground'>{droneResult.processed_frames} Frames ({droneResult.scan_mode || '15 FPS'})</span>
                  </div>
                  <div className='flex items-center justify-between font-sans text-xs'>
                    <span className='text-muted-foreground'>Compute Conserved:</span>
                    <span className='font-bold text-primary'>
                      {droneResult.estimated_compute_reduction?.toFixed(1) || 0}% Saved
                    </span>
                  </div>

                  {/* Video Player or Thumbnail */}
                  <div className='rounded-md overflow-hidden border border-border bg-black/60 h-32 flex items-center justify-center text-xs text-muted-foreground'>
                    {annotVideoUrl ? (
                      <video src={annotVideoUrl} controls className='w-full h-full object-cover' />
                    ) : (
                      <span>Tracking video ready</span>
                    )}
                  </div>
                </div>
              ) : (
                <div className='py-8 text-center text-muted-foreground font-sans space-y-3'>
                  <Radio className='size-10 mx-auto text-muted-foreground/40' />
                  <p className='text-xs'>No video processed yet.</p>
                  <Button asChild size='sm' className='font-sans text-xs bg-primary text-primary-foreground hover:bg-primary/90'>
                    <Link to='/tracking'>
                      <Play className='size-3 mr-1.5' /> Track vessels
                    </Link>
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* LATEST INTELLIGENCE BRIEFING */}
        <Card className='bg-card/90 border-border'>
          <CardHeader className='pb-2 border-b border-border/50 flex flex-row items-center justify-between'>
            <div className='flex items-center gap-2'>
              <Bot className='size-4 text-primary' />
              <CardTitle className='text-xs font-sans font-semibold tracking-normal normal-case text-foreground'>
                Image analysis
              </CardTitle>
            </div>
            <Button asChild size='sm' variant='ghost' className='font-sans text-xs text-primary'>
              <Link to='/intelligence'>
                View analysis <ArrowRight className='size-3 ml-1' />
              </Link>
            </Button>
          </CardHeader>
          <CardContent className='p-4 text-xs font-sans leading-relaxed text-muted-foreground'>
            {vlmText ? (
              <div className='p-3.5 rounded-md bg-secondary/40 border border-primary/20 text-foreground whitespace-pre-line'>
                <p className='font-bold text-primary mb-1 text-[11px]'>BRIEFING REPORT:</p>
                {vlmText}
              </div>
            ) : (
              <div className='p-4 rounded-md bg-secondary/30 border border-border/60 text-muted-foreground text-center'>
                Analyze an image or track a video to see a summary here.
              </div>
            )}
          </CardContent>
        </Card>
      </Main>
    </>
  )
}
