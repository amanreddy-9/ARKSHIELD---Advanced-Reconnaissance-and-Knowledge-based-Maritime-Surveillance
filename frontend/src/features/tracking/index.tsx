import { useEffect, useState } from 'react'

import {

  AlertCircle,

  Loader2,

  Play,

  Radio,

  Sliders,

  UploadCloud,

  Video,

} from 'lucide-react'

import { TrackingPresentation } from '@/components/tracking-presentation'

import { Header } from '@/components/layout/header'

import { Main } from '@/components/layout/main'

import { ProfileDropdown } from '@/components/profile-dropdown'

import { Search } from '@/components/search'

import { ThemeSwitch } from '@/components/theme-switch'

import { Badge } from '@/components/ui/badge'

import { Button } from '@/components/ui/button'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

import { Label } from '@/components/ui/label'

import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

import { Checkbox } from '@/components/ui/checkbox'

import {

  getDronePresets,

  processDronePresetVideo,

  processDroneVideo,

} from '@/api/drone'

import { resolveBackendUrl } from '@/api/client'

import { DronePreset } from '@/api/types'

import { useSurveillanceStore } from '@/stores/surveillance-store'



export function TrackingFeature() {

  const { droneResult, setDroneResult } = useSurveillanceStore()



  const [presets, setPresets] = useState<DronePreset[]>([])

  const [selectedPresetId, setSelectedPresetId] = useState<string>('frigate_patrol')

  const [uploadedFile, setUploadedFile] = useState<File | null>(null)



  const [speedMode, setSpeedMode] = useState<number>(2) // 2 = 15 FPS Fast Scan, 1 = 30 FPS Full Scan

  const [quickPreview, setQuickPreview] = useState<boolean>(false)



  const [loading, setLoading] = useState<boolean>(false)

  const [error, setError] = useState<string | null>(null)



  useEffect(() => {

    getDronePresets().then((data) => {

      setPresets(data)

      if (data.length > 0) {

        setSelectedPresetId(data[0].id)

      }

    })

  }, [])



  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {

    if (e.target.files && e.target.files[0]) {

      setUploadedFile(e.target.files[0])

      setSelectedPresetId('custom')

    }

  }



  const handleExecuteTracking = async () => {

    setLoading(true)

    setError(null)

    try {

      const maxFrames = quickPreview ? 150 : null

      if (selectedPresetId === 'custom' && uploadedFile) {

        const res = await processDroneVideo({

          file: uploadedFile,

          target_x: 0,

          target_y: 0,

          sample_every: speedMode,

        })

        setDroneResult(res)

      } else {

        const res = await processDronePresetVideo(selectedPresetId, {

          target_x: 0,

          target_y: 0,

          sample_every: speedMode,

          max_frames: maxFrames,

        })

        setDroneResult(res)

      }

    } catch (err: any) {

      setError(err?.message || 'UAV tracking execution failed.')

    } finally {

      setLoading(false)

    }

  }



  const annotVideoUrl = droneResult?.annotated_video_url

    ? resolveBackendUrl(droneResult.annotated_video_url)

    : null



  const primary = droneResult?.primary_vessel

  const trackSummaries = droneResult?.track_summaries || {}
  const currentTracks = Object.entries(trackSummaries).filter(([,tr]) => tr.lifecycle_state !== 'deleted')
  const historicalTracks = Object.entries(trackSummaries).filter(([,tr]) => tr.lifecycle_state === 'deleted')
  const counts = droneResult?.track_state_counts




  return (

    <>

      <Header fixed>

        <div className='flex items-center gap-2'>

          <Radio className='size-5 text-primary' />

          <div>

            <h1 className='text-sm font-bold tracking-normal font-sans text-foreground normal-case'>

              Vessel tracking

            </h1>

            <p className='text-[10px] font-sans text-muted-foreground'>

              Upload a drone video to detect vessels and follow their movement.

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

        <TrackingPresentation />

        {/* Top Telemetry KPI Bar */}

        {droneResult && (

          <div className='grid grid-cols-2 md:grid-cols-4 gap-3'>

            <Card className='bg-card border-border p-3'>

              <span className='font-sans text-[10px] text-muted-foreground normal-case'>Estimated Class</span>

              <p className='font-sans text-lg font-bold text-emerald-400 mt-1 truncate'>

                {primary?.display_label || primary?.label || 'Vessel'}

              </p>

              <p className='font-sans text-[10px] text-muted-foreground mt-0.5'>ConvNeXt-Tiny FGS-10</p>

            </Card>



            <Card className='bg-card border-border p-3'>

              <span className='font-sans text-[10px] text-muted-foreground normal-case'>Primary Track ID</span>

              <p className='font-sans text-lg font-bold text-primary mt-1'>

                Track #{primary?.track_id || 1}

              </p>

              <p className='font-sans text-[10px] text-muted-foreground mt-0.5'>Continuous Kalman State</p>

            </Card>



            <Card className='bg-card border-border p-3'>

              <span className='font-sans text-[10px] text-muted-foreground normal-case'>Evidence Stability</span>

              <p className='font-sans text-lg font-bold text-primary mt-1'>

                {primary?.stability ? `${(primary.stability * 100).toFixed(1)}%` : 'N/A'}

              </p>

              <p className='font-sans text-[10px] text-muted-foreground mt-0.5'>

                {primary?.observations || 0} Observation Votes

              </p>

            </Card>



            <Card className='bg-card border-border p-3'>

              <span className='font-sans text-[10px] text-muted-foreground normal-case'>Compute Conserved</span>

              <p className='font-sans text-lg font-bold text-amber-400 mt-1'>

                {droneResult.estimated_compute_reduction?.toFixed(1) || 0}%

              </p>

              <p className='font-sans text-[10px] text-muted-foreground mt-0.5'>PPO Policy Frequency</p>

            </Card>

          </div>

        )}



        {/* Main Workstation Layout */}

        <div className='grid grid-cols-1 lg:grid-cols-12 gap-4'>

          {/* LEFT: Controls (4 cols) */}

          <div className='lg:col-span-4 space-y-4'>

            <Card className='bg-card/90 border-border'>

              <CardHeader className='pb-3 border-b border-border/50'>

                <CardTitle className='text-xs font-sans font-semibold tracking-normal normal-case text-foreground flex items-center gap-2'>

                  <Sliders className='size-4 text-primary' />

                  Video settings

                </CardTitle>

              </CardHeader>

              <CardContent className='p-4 space-y-4'>

                {/* Preset Selector */}

                <div className='space-y-1.5'>

                  <Label className='text-xs font-sans text-muted-foreground'>

                    Drone Video Feed Preset:

                  </Label>

                  <Select

                    value={selectedPresetId}

                    onValueChange={(val) => {

                      setSelectedPresetId(val)

                      if (val !== 'custom') setUploadedFile(null)

                    }}

                  >

                    <SelectTrigger className='text-xs font-sans bg-secondary/50'>

                      <SelectValue placeholder='Select Video Feed' />

                    </SelectTrigger>

                    <SelectContent className='text-xs font-sans'>

                      <SelectItem value='custom'>-- Upload Custom Drone Video --</SelectItem>

                      {presets.map((p) => (

                        <SelectItem key={p.id} value={p.id}>

                          {p.name}

                        </SelectItem>

                      ))}

                    </SelectContent>

                  </Select>

                </div>



                {/* Upload Box (if custom) */}

                {selectedPresetId === 'custom' && (

                  <div className='space-y-1.5 pt-1'>

                    <Label className='text-xs font-sans text-muted-foreground'>

                      Upload Drone Video (MP4, AVI, MOV):

                    </Label>

                    <label className='flex flex-col items-center justify-center border-2 border-dashed border-border hover:border-primary/60 rounded-lg p-4 cursor-pointer bg-secondary/20 transition-colors'>

                      <UploadCloud className='size-6 text-primary mb-1' />

                      <span className='text-xs font-sans text-foreground'>

                        {uploadedFile ? uploadedFile.name : 'Click to select video'}

                      </span>

                      <span className='text-[10px] text-muted-foreground font-sans mt-0.5'>

                        MP4, AVI, MOV accepted

                      </span>

                      <input

                        type='file'

                        accept='video/mp4,video/avi,video/quicktime,video/x-matroska'

                        className='hidden'

                        onChange={handleFileChange}

                      />

                    </label>

                  </div>

                )}



                {/* Tracking Speed Optimization */}

                <div className='space-y-2 pt-1'>

                  <Label className='text-xs font-sans text-muted-foreground'>

                    Tracking Cadence & Speed Mode:

                  </Label>

                  <RadioGroup

                    value={speedMode.toString()}

                    onValueChange={(val) => setSpeedMode(parseInt(val, 10))}

                    className='space-y-2 text-xs font-sans'

                  >

                    <div className='flex items-center space-x-2 p-2 rounded border border-border/60 bg-secondary/20'>

                      <RadioGroupItem value='2' id='sp2' />

                      <Label htmlFor='sp2' className='cursor-pointer flex-1'>

                        <span className='font-bold text-foreground'>15 FPS Fast Scan</span>

                        <p className='text-[10px] text-muted-foreground'>Alternate frames (Smooth Kalman coasting)</p>

                      </Label>

                    </div>

                    <div className='flex items-center space-x-2 p-2 rounded border border-border/60 bg-secondary/20'>

                      <RadioGroupItem value='1' id='sp1' />

                      <Label htmlFor='sp1' className='cursor-pointer flex-1'>

                        <span className='font-bold text-foreground'>30 FPS Full Scan</span>

                        <p className='text-[10px] text-muted-foreground'>Exhaustive frame-by-frame evaluation</p>

                      </Label>

                    </div>

                  </RadioGroup>

                </div>



                {/* Quick Mission Preview */}

                <div className='flex items-center space-x-2 pt-1'>

                  <Checkbox

                    id='quick-prev'

                    checked={quickPreview}

                    onCheckedChange={(c) => setQuickPreview(!!c)}

                  />

                  <Label htmlFor='quick-prev' className='text-xs font-sans cursor-pointer text-muted-foreground'>

                    Quick preview (150 frames)

                  </Label>

                </div>



                {/* Execute button */}

                <Button

                  onClick={handleExecuteTracking}

                  disabled={loading}

                  className='w-full font-sans text-xs bg-primary text-primary-foreground hover:bg-primary/90 mt-2'

                >

                  {loading ? (

                    <>

                      <Loader2 className='size-4 mr-2 animate-spin' /> Running Continuous Tracking...

                    </>

                  ) : (

                    <>

                      <Play className='size-4 mr-2' /> Execute Drone Surveillance

                    </>

                  )}

                </Button>



                {error && (

                  <div className='p-3 rounded-md bg-destructive/15 border border-destructive/30 text-destructive text-xs font-sans flex items-start gap-2'>

                    <AlertCircle className='size-4 shrink-0 mt-0.5' />

                    <span>{error}</span>

                  </div>

                )}

              </CardContent>

            </Card>



            {/* Tactical HUD Legend */}

            <Card className='bg-card/90 border-border'>

              <CardHeader className='pb-2 border-b border-border/50'>

                <CardTitle className='text-xs font-sans font-semibold tracking-normal normal-case text-foreground'>

                  Video legend

                </CardTitle>

              </CardHeader>

              <CardContent className='p-3 font-sans text-xs space-y-2 text-muted-foreground'>

                <div className='flex items-center gap-2'>

                  <div className='size-3 rounded-sm border-2 border-emerald-400' />

                  <span>Solid green box: current detection</span>

                </div>

                <div className='flex items-center gap-2'>

                  <div className='size-3 rounded-sm bg-cyan-400/30 border border-cyan-400' />

                  <span>Cyan label: persistent vessel ID and class</span>

                </div>

                <div className='flex items-center gap-2'>

                  <div className='size-3 rounded-sm border-2 border-dashed border-amber-400' />

                  <span>Dashed amber box: predicted position</span>

                </div>

              </CardContent>

            </Card>

          </div>



          {/* CENTER: Video Playback Area (8 cols) */}

          <div className='lg:col-span-8 space-y-4'>

            <Card className='bg-card/90 border-border overflow-hidden'>

              <CardHeader className='pb-2 border-b border-border/50 flex flex-row items-center justify-between'>

                <CardTitle className='text-xs font-sans font-semibold tracking-normal normal-case text-foreground flex items-center gap-2'>

                  <Video className='size-4 text-primary' />

                  Tracking video

                </CardTitle>

                {droneResult && (

                  <Badge variant='outline' className='font-sans text-xs border-emerald-500/40 text-emerald-400'>

                    {droneResult.processed_frames} FRAMES PROCESSED

                  </Badge>

                )}

              </CardHeader>

              <CardContent className='p-4'>

                <div className='min-h-[440px] flex items-center justify-center bg-black/80 rounded-lg border border-border p-2'>

                  {annotVideoUrl ? (

                    <video

                      src={annotVideoUrl}

                      controls

                      autoPlay

                      loop

                      className='max-h-[540px] w-full rounded object-contain'

                    />

                  ) : (

                    <div className='text-center py-16 text-muted-foreground font-sans space-y-3'>

                      <Video className='size-12 mx-auto text-muted-foreground/30' />

                      <p className='text-xs'>

                        Select a drone sequence preset and click "Execute Drone Surveillance".

                      </p>

                      <p className='text-[10px] text-muted-foreground/80'>

                        The backend renders bounding boxes, track IDs, and movement trails into an H.264 stream.

                      </p>

                    </div>

                  )}

                </div>

              </CardContent>

            </Card>

          </div>

        </div>



        {/* BOTTOM: Vessel tracks Table */}

        {Object.keys(trackSummaries).length > 0 && (

          <div className='space-y-4'>
          <p className='text-sm text-muted-foreground'>At video end: {counts?.confirmed_detected ?? currentTracks.filter(([,tr]) => ['confirmed','recovered'].includes(tr.lifecycle_state || '')).length} confirmed detections · {counts?.coasting ?? currentTracks.filter(([,tr]) => tr.lifecycle_state === 'coasting').length} coasting · {counts?.tentative ?? currentTracks.filter(([,tr]) => tr.lifecycle_state === 'tentative').length} tentative · {historicalTracks.length} deleted historical records</p>
          {[{ title: 'Current tracks at video end', entries: currentTracks }, { title: 'Deleted track history', entries: historicalTracks }].map(({title, entries}) => (
          <Card key={title} className='bg-card/90 border-border'>

            <CardHeader className='pb-3 border-b border-border/50 flex flex-row items-center justify-between'>

              <div>

                <CardTitle className='text-xs font-sans font-semibold tracking-normal normal-case text-foreground'>

                  {title} ({entries.length})

                </CardTitle>

                <p className='text-[11px] text-muted-foreground font-sans'>

                  Tracking state is separate from classification certainty; historical IDs are not current vessels.

                </p>

              </div>

            </CardHeader>

            <CardContent className='p-0 overflow-x-auto'>

              <Table>

                <TableHeader>

                  <TableRow className='border-border/60 font-sans text-[11px] text-muted-foreground'>

                    <TableHead>Track ID</TableHead>

                    <TableHead>Vessel Classification</TableHead>

                    <TableHead>Model Score Share</TableHead>

                    <TableHead>Tracking / Classification observations</TableHead>

                    <TableHead>VLM reasoning</TableHead>

                    <TableHead>Tracking Status</TableHead>

                    <TableHead>Last Seen Frame</TableHead>

                  </TableRow>

                </TableHeader>

                <TableBody className='font-sans text-xs'>

                  {entries

                    .sort(([a], [b]) => parseInt(a, 10) - parseInt(b, 10))

                    .map(([tidStr, tr]) => {

                      const obs = tr.observations

                      const stab = tr.stability * 100

                      const isConfirmed = tr.confirmed_identity ?? ['confirmed','recovered','coasting'].includes(tr.lifecycle_state || '')

                      const trackingStatus = tr.lifecycle_state || 'unknown'



                      return (

                        <TableRow key={tidStr} className='border-border/40 hover:bg-muted/40'>

                          <TableCell className='font-bold text-primary'>

                            Track #{String(tr.track_id).padStart(2, '0')}

                          </TableCell>

                          <TableCell className='font-semibold text-foreground'>

                            {tr.display_label || tr.label}

                          </TableCell>

                          <TableCell>

                            <span

                              className={`px-1.5 py-0.5 rounded text-[11px] ${

                                stab >= 75

                                  ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'

                                  : 'bg-red-500/15 text-primary border border-primary/30'

                              }`}

                            >

                              {stab.toFixed(1)}%

                            </span>

                          </TableCell>

                          <TableCell className='text-muted-foreground'>{tr.tracking_observations ?? 'N/A'} / {obs}</TableCell>

                          <TableCell title={tr.vlm?.reasoning} className='text-muted-foreground'>

                            {tr.vlm?.source === 'cached' ? `Cached · ${tr.vlm.label}` :

                              tr.vlm?.source === 'fresh' ? 'Fresh' :

                              tr.vlm?.source === 'unavailable' ? 'Unavailable · ConvNeXt fallback' :

                              tr.vlm?.source === 'disabled' ? 'Disabled' : 'Not requested'}

                            {tr.vlm?.reasoning && <p className='text-xs max-w-xs mt-1'>{tr.vlm.reasoning}</p>}

                          </TableCell>

                          <TableCell>

                            <span

                              className={`px-1.5 py-0.5 rounded text-[10px] normal-case font-bold ${

                                isConfirmed

                                  ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'

                                  : 'bg-amber-500/15 text-amber-400 border border-amber-500/30'

                              }`}

                            >

                              {trackingStatus.toUpperCase()}

                            </span>

                          </TableCell>

                          <TableCell title={tr.deletion_reason ? `Deleted at frame ${tr.deletion_frame}: ${tr.deletion_reason}` : undefined} className='text-muted-foreground'>

                            Frm {tr.last_measurement_frame ?? tr.last_seen_frame ?? 'N/A'}

                          </TableCell>

                        </TableRow>

                      )

                    })}

                </TableBody>

              </Table>

            </CardContent>

          </Card>
          ))}
          </div>

        )}

      </Main>

    </>

  )

}

