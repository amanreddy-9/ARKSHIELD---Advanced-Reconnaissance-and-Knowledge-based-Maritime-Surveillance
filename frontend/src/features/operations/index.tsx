import { Link } from '@tanstack/react-router'
import {
  Compass,
  Radio,
  Satellite,
  Video,
} from 'lucide-react'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { resolveBackendUrl } from '@/api/client'
import { useSurveillanceStore } from '@/stores/surveillance-store'

export function OperationsFeature() {
  const { satelliteResult, droneResult } = useSurveillanceStore()

  const annotSatUrl = satelliteResult?.annotated_image_url
    ? resolveBackendUrl(satelliteResult.annotated_image_url)
    : null

  const annotVideoUrl = droneResult?.annotated_video_url
    ? resolveBackendUrl(droneResult.annotated_video_url)
    : null

  return (
    <>
      <Header fixed>
        <div className='flex items-center gap-2'>
          <Compass className='size-5 text-primary' />
          <div>
            <h1 className='text-sm font-bold tracking-normal font-sans text-foreground normal-case'>
              Live Tactical Operations Console
            </h1>
            <p className='text-[10px] font-sans text-muted-foreground'>
              Synchronized Wide-Area Satellite Detection & Close-Quarters Video tracking
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
        {/* Status Ribbon */}
        <div className='flex flex-wrap items-center justify-between gap-2 p-3 rounded-lg bg-card border border-border text-xs font-sans'>
          <div className='flex items-center gap-2'>
            <span className='inline-block size-2 rounded-full bg-emerald-400 animate-ping' />
            <span className='font-bold text-foreground'>TACTICAL OPERATION READY</span>
          </div>
          <div className='flex items-center gap-2'>
            <Badge variant='outline' className='font-sans text-primary border-red-500/40'>
              SATELLITE: {satelliteResult ? `${satelliteResult.ship_count} TARGETS` : 'STANDBY'}
            </Badge>
            <Badge variant='outline' className='font-sans text-emerald-400 border-emerald-500/40'>
              UAV: {droneResult ? `${droneResult.unique_track_count} TRACKS` : 'STANDBY'}
            </Badge>
            <Badge variant='outline' className='font-sans text-amber-400 border-amber-500/40'>
              PPO COMPUTE: {droneResult ? `${droneResult.estimated_compute_reduction?.toFixed(1)}% SAVED` : 'STANDBY'}
            </Badge>
          </div>
        </div>

        {/* Dual Unified Video/Image Screen */}
        <div className='grid grid-cols-1 lg:grid-cols-2 gap-4'>
          {/* LEFT: SATELLITE TACTICAL DISPLAY */}
          <Card className='bg-card/90 border-border'>
            <CardHeader className='pb-2 border-b border-border/50 flex flex-row items-center justify-between'>
              <div className='flex items-center gap-2'>
                <Satellite className='size-4 text-primary' />
                <CardTitle className='text-xs font-sans font-semibold normal-case'>
                  Satellite Optical Coordinate Map
                </CardTitle>
              </div>
              <Button asChild size='sm' variant='ghost' className='font-sans text-xs text-primary'>
                <Link to='/satellite'>Manage Scan</Link>
              </Button>
            </CardHeader>
            <CardContent className='p-4'>
              <div className='h-[420px] bg-black/70 rounded-lg border border-border flex items-center justify-center p-2'>
                {annotSatUrl ? (
                  <img src={annotSatUrl} alt='Satellite Detections' className='max-h-full w-full object-contain rounded' />
                ) : (
                  <div className='text-center font-sans text-xs text-muted-foreground space-y-2'>
                    <Satellite className='size-10 mx-auto text-muted-foreground/30' />
                    <p>No satellite targets loaded in session.</p>
                    <Button asChild size='sm' variant='outline' className='font-sans text-xs'>
                      <Link to='/satellite'>Load Satellite Imagery</Link>
                    </Button>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* RIGHT: TACTICAL DRONE VIDEO STREAM */}
          <Card className='bg-card/90 border-border'>
            <CardHeader className='pb-2 border-b border-border/50 flex flex-row items-center justify-between'>
              <div className='flex items-center gap-2'>
                <Video className='size-4 text-emerald-400' />
                <CardTitle className='text-xs font-sans font-semibold normal-case'>
                  Tactical UAV Video Telemetry
                </CardTitle>
              </div>
              <Button asChild size='sm' variant='ghost' className='font-sans text-xs text-primary'>
                <Link to='/tracking'>Manage Tracking</Link>
              </Button>
            </CardHeader>
            <CardContent className='p-4'>
              <div className='h-[420px] bg-black/70 rounded-lg border border-border flex items-center justify-center p-2'>
                {annotVideoUrl ? (
                  <video src={annotVideoUrl} controls autoPlay loop className='max-h-full w-full object-contain rounded' />
                ) : (
                  <div className='text-center font-sans text-xs text-muted-foreground space-y-2'>
                    <Radio className='size-10 mx-auto text-muted-foreground/30' />
                    <p>No tactical drone stream active in session.</p>
                    <Button asChild size='sm' variant='outline' className='font-sans text-xs'>
                      <Link to='/tracking'>Launch Drone Feed</Link>
                    </Button>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* BOTTOM: Integrated Operations Telemetry */}
        <div className='grid grid-cols-1 md:grid-cols-3 gap-4'>
          <Card className='bg-card/90 border-border p-4 space-y-2'>
            <span className='font-sans text-[10px] text-muted-foreground normal-case'>Satellite Sensor Status</span>
            <div className='font-sans text-xs text-foreground space-y-1'>
              <div className='flex justify-between'>
                <span className='text-muted-foreground'>Targets in Frame:</span>
                <span className='font-bold text-primary'>{satelliteResult?.ship_count ?? 0} Vessels</span>
              </div>
              <div className='flex justify-between'>
                <span className='text-muted-foreground'>Resolution:</span>
                <span>1024 × 1024 px</span>
              </div>
              <div className='flex justify-between'>
                <span className='text-muted-foreground'>Detector Model:</span>
                <span className='truncate'>{satelliteResult?.model_variant || 'YOLO11n-VHRV'}</span>
              </div>
            </div>
          </Card>

          <Card className='bg-card/90 border-border p-4 space-y-2'>
            <span className='font-sans text-[10px] text-muted-foreground normal-case'>Tactical UAV Status</span>
            <div className='font-sans text-xs text-foreground space-y-1'>
              <div className='flex justify-between'>
                <span className='text-muted-foreground'>Primary Target:</span>
                <span className='font-bold text-emerald-400'>{droneResult?.primary_vessel?.label || 'None'}</span>
              </div>
              <div className='flex justify-between'>
                <span className='text-muted-foreground'>Active Tracks:</span>
                <span>{droneResult?.unique_track_count ?? 0}</span>
              </div>
              <div className='flex justify-between'>
                <span className='text-muted-foreground'>Frames Processed:</span>
                <span>{droneResult?.processed_frames ?? 0}</span>
              </div>
            </div>
          </Card>

          <Card className='bg-card/90 border-border p-4 space-y-2'>
            <span className='font-sans text-[10px] text-muted-foreground normal-case'>PPO Compute Throttle</span>
            <div className='font-sans text-xs text-foreground space-y-1'>
              <div className='flex justify-between'>
                <span className='text-muted-foreground'>Compute Conserved:</span>
                <span className='font-bold text-amber-400'>{droneResult?.estimated_compute_reduction?.toFixed(1) || 0}%</span>
              </div>
              <div className='flex justify-between'>
                <span className='text-muted-foreground'>Safety Overrides:</span>
                <span>{droneResult?.safety_overrides ?? 0} Triggers</span>
              </div>
              <div className='flex justify-between'>
                <span className='text-muted-foreground'>Scheduler Engine:</span>
                <span>Gymnasium + SB3 PPO</span>
              </div>
            </div>
          </Card>
        </div>
      </Main>
    </>
  )
}
