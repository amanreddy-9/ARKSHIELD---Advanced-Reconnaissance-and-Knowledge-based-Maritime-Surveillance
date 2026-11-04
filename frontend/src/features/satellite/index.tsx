import { useEffect, useState } from 'react'
import {
  AlertCircle,
  CheckCircle2,
  Eye,
  Loader2,
  Play,
  Satellite,
  Sliders,
  UploadCloud,
} from 'lucide-react'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Slider } from '@/components/ui/slider'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  detectSatelliteImage,
  detectSatellitePreset,
  getSatellitePresets,
} from '@/api/satellite'
import { resolveBackendUrl } from '@/api/client'
import { SatellitePreset } from '@/api/types'
import { useSurveillanceStore } from '@/stores/surveillance-store'

export function SatelliteFeature() {
  const { satelliteResult, setSatelliteResult } = useSurveillanceStore()

  const [presets, setPresets] = useState<SatellitePreset[]>([])
  const [selectedPresetId, setSelectedPresetId] = useState<string>('frigate_optical')
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)

  const [weights, setWeights] = useState<string>(
    'Custom Fine-Tuned (models/weights/vhrv_custom_best.pt) [Best Accuracy]'
  )
  const [confThreshold, setConfThreshold] = useState<number>(0.25)
  const [iouThreshold, setIouThreshold] = useState<number>(0.60)

  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [activeView, setActiveView] = useState<'annotated' | 'raw' | 'split'>('annotated')

  useEffect(() => {
    getSatellitePresets().then((data) => {
      setPresets(data)
      if (data.length > 0) {
        setSelectedPresetId(data[0].id)
      }
    })
  }, [])

  // Handle local file selection
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0]
      setUploadedFile(file)
      setSelectedPresetId('custom')
      const objUrl = URL.createObjectURL(file)
      setPreviewUrl(objUrl)
    }
  }

  // Run Satellite Detection
  const handleRunDetection = async () => {
    setLoading(true)
    setError(null)
    try {
      if (selectedPresetId === 'custom' && uploadedFile) {
        const res = await detectSatelliteImage({
          file: uploadedFile,
          weights,
          conf: confThreshold,
          iou: iouThreshold,
        })
        setSatelliteResult(res)
      } else {
        const res = await detectSatellitePreset(selectedPresetId, {
          weights,
          conf: confThreshold,
          iou: iouThreshold,
        })
        setSatelliteResult(res)
      }
    } catch (err: any) {
      setError(err?.message || 'Satellite detection failed.')
    } finally {
      setLoading(false)
    }
  }

  const rawUrl = uploadedFile && previewUrl
    ? previewUrl
    : satelliteResult?.raw_image_url
      ? resolveBackendUrl(satelliteResult.raw_image_url)
      : null

  const annotUrl = satelliteResult?.annotated_image_url
    ? resolveBackendUrl(satelliteResult.annotated_image_url)
    : null

  const vlmText = typeof satelliteResult?.vlm_analysis === 'string'
    ? satelliteResult.vlm_analysis
    : (satelliteResult?.vlm_analysis as any)?.text || (satelliteResult?.vlm_analysis as any)?.briefing || null

  return (
    <>
      <Header fixed>
        <div className='flex items-center gap-2'>
          <Satellite className='size-5 text-primary' />
          <div>
            <h1 className='text-sm font-bold tracking-normal font-sans text-foreground normal-case'>
              Satellite vessel detection
            </h1>
            <p className='text-[10px] font-sans text-muted-foreground'>
              Select an image to find and count vessels.
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
        {/* Top telemetry status */}
        {satelliteResult && (
          <div className='flex flex-wrap items-center gap-2 p-2.5 rounded-lg bg-card border border-border text-xs font-sans'>
            <span className='hud-badge hud-badge-cyan'>
              MODEL: {satelliteResult.model_variant || 'YOLO11n-VHRV'}
            </span>
            <span className='hud-badge hud-badge-green'>
              VESSELS: {satelliteResult.ship_count} Targets
            </span>
            <span className='hud-badge hud-badge-amber'>
              CONF: {(satelliteResult.conf_threshold ?? confThreshold).toFixed(2)}
            </span>
            <span className='hud-badge hud-badge-green'>
              IOU: {(satelliteResult.iou_threshold ?? iouThreshold).toFixed(2)}
            </span>
            {satelliteResult.processing_time_ms && (
              <span className='hud-badge hud-badge-blue ml-auto'>
                LATENCY: {satelliteResult.processing_time_ms} ms
              </span>
            )}
          </div>
        )}

        {/* 3-Column Workstation Layout */}
        <div className='grid grid-cols-1 lg:grid-cols-12 gap-4'>
          {/* LEFT: Controls (4 cols) */}
          <div className='lg:col-span-4 space-y-4'>
            <Card className='bg-card/90 border-border'>
              <CardHeader className='pb-3 border-b border-border/50'>
                <CardTitle className='text-xs font-sans font-semibold tracking-normal normal-case text-foreground flex items-center gap-2'>
                  <Sliders className='size-4 text-primary' />
                  Image settings
                </CardTitle>
              </CardHeader>
              <CardContent className='p-4 space-y-4'>
                {/* Preset Selector */}
                <div className='space-y-1.5'>
                  <Label className='text-xs font-sans text-muted-foreground'>
                    Satellite Target Preset:
                  </Label>
                  <Select
                    value={selectedPresetId}
                    onValueChange={(val) => {
                      setSelectedPresetId(val)
                      if (val !== 'custom') {
                        setUploadedFile(null)
                        setPreviewUrl(null)
                      }
                    }}
                  >
                    <SelectTrigger className='text-xs font-sans bg-secondary/50'>
                      <SelectValue placeholder='Select Satellite Preset' />
                    </SelectTrigger>
                    <SelectContent className='text-xs font-sans'>
                      <SelectItem value='custom'>-- Upload Custom Satellite Image --</SelectItem>
                      {presets.map((p) => (
                        <SelectItem key={p.id} value={p.id}>
                          {p.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* File Upload Box (if Custom is chosen) */}
                {selectedPresetId === 'custom' && (
                  <div className='space-y-1.5 pt-1'>
                    <Label className='text-xs font-sans text-muted-foreground'>
                      Upload Satellite Image (JPG/PNG):
                    </Label>
                    <label className='flex flex-col items-center justify-center border-2 border-dashed border-border hover:border-primary/60 rounded-lg p-4 cursor-pointer bg-secondary/20 transition-colors'>
                      <UploadCloud className='size-6 text-primary mb-1' />
                      <span className='text-xs font-sans text-foreground'>
                        {uploadedFile ? uploadedFile.name : 'Click to select image'}
                      </span>
                      <span className='text-[10px] text-muted-foreground font-sans mt-0.5'>
                        Supports up to 4800×2886 optical imagery
                      </span>
                      <input
                        type='file'
                        accept='image/jpeg,image/png,image/jpg'
                        className='hidden'
                        onChange={handleFileChange}
                      />
                    </label>
                  </div>
                )}

                {/* Model Weights */}
                <div className='space-y-1.5'>
                  <Label className='text-xs font-sans text-muted-foreground'>
                    YOLO11n Detector Weights:
                  </Label>
                  <Select value={weights} onValueChange={setWeights}>
                    <SelectTrigger className='text-xs font-sans bg-secondary/50'>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className='text-xs font-sans'>
                      <SelectItem value='Custom Fine-Tuned (models/weights/vhrv_custom_best.pt) [Best Accuracy]'>
                        Fine-Tuned (vhrv_custom_best.pt) [96.8% mAP]
                      </SelectItem>
                      <SelectItem value='Baseline (models/weights/vhrv_best.pt)'>
                        Baseline (vhrv_best.pt) [94.6% mAP]
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Confidence Threshold */}
                <div className='space-y-2 pt-1'>
                  <div className='flex justify-between text-xs font-sans'>
                    <Label className='text-muted-foreground'>Confidence Threshold:</Label>
                    <span className='text-primary font-bold'>{confThreshold.toFixed(2)}</span>
                  </div>
                  <Slider
                    min={0.1}
                    max={0.9}
                    step={0.05}
                    value={[confThreshold]}
                    onValueChange={(val) => setConfThreshold(val[0])}
                  />
                </div>

                {/* NMS IoU Threshold */}
                <div className='space-y-2 pt-1'>
                  <div className='flex justify-between text-xs font-sans'>
                    <Label className='text-muted-foreground'>NMS IoU Threshold:</Label>
                    <span className='text-emerald-400 font-bold'>{iouThreshold.toFixed(2)}</span>
                  </div>
                  <Slider
                    min={0.3}
                    max={0.85}
                    step={0.05}
                    value={[iouThreshold]}
                    onValueChange={(val) => setIouThreshold(val[0])}
                  />
                </div>

                {/* Action button */}
                <Button
                  onClick={handleRunDetection}
                  disabled={loading}
                  className='w-full font-sans text-xs bg-primary text-primary-foreground hover:bg-primary/90 mt-2'
                >
                  {loading ? (
                    <>
                      <Loader2 className='size-4 mr-2 animate-spin' /> Running High-Res YOLO11n (1024px)...
                    </>
                  ) : (
                    <>
                      <Play className='size-4 mr-2' /> Execute Satellite Detection
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

            {/* Tactical Briefing Box */}
            <Card className='bg-card/90 border-border'>
              <CardHeader className='pb-2 border-b border-border/50'>
                <CardTitle className='text-xs font-sans font-semibold tracking-normal normal-case text-primary flex items-center gap-2'>
                  <CheckCircle2 className='size-4 text-primary' />
                  Image summary
                </CardTitle>
              </CardHeader>
              <CardContent className='p-4 text-xs font-sans leading-relaxed text-muted-foreground'>
                {vlmText ? (
                  <div className='p-3 rounded-md bg-secondary/50 border border-primary/20 text-foreground whitespace-pre-line'>
                    {typeof satelliteResult?.vlm_analysis === 'object' && (
                      <span className='block text-xs text-muted-foreground mb-2'>
                        VLM: {satelliteResult.vlm_analysis.status === 'OK'
                          ? satelliteResult.vlm_analysis.source || 'fresh'
                          : 'unavailable'}
                      </span>
                    )}
                    {vlmText}
                  </div>
                ) : (
                  <p className='italic text-center py-4'>
                    Briefing will synthesize automatically upon running detection.
                  </p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* CENTER: High-Res Image Viewers (8 cols) */}
          <div className='lg:col-span-8 space-y-4'>
            <Card className='bg-card/90 border-border overflow-hidden'>
              <CardHeader className='pb-2 border-b border-border/50 flex flex-row items-center justify-between'>
                <CardTitle className='text-xs font-sans font-semibold tracking-normal normal-case text-foreground flex items-center gap-2'>
                  <Eye className='size-4 text-primary' />
                  Image preview
                </CardTitle>
                <div className='flex items-center gap-2'>
                  <Tabs value={activeView} onValueChange={(v: any) => setActiveView(v)} className='w-auto'>
                    <TabsList className='h-7 bg-secondary/50 text-[11px] font-sans'>
                      <TabsTrigger value='annotated' className='h-5 px-2 text-[11px]'>
                        Bounding Boxes
                      </TabsTrigger>
                      <TabsTrigger value='raw' className='h-5 px-2 text-[11px]'>
                        Raw Feed
                      </TabsTrigger>
                      <TabsTrigger value='split' className='h-5 px-2 text-[11px]'>
                        Side-by-Side
                      </TabsTrigger>
                    </TabsList>
                  </Tabs>
                </div>
              </CardHeader>
              <CardContent className='p-4'>
                {activeView === 'split' ? (
                  <div className='grid grid-cols-1 md:grid-cols-2 gap-3 min-h-[420px]'>
                    <div className='flex flex-col space-y-1.5'>
                      <span className='text-[11px] font-sans text-muted-foreground font-semibold'>
                        Original Satellite Optical Sensor Feed
                      </span>
                      <div className='flex-1 rounded-md overflow-hidden border border-border bg-black/50 flex items-center justify-center p-1'>
                        {rawUrl ? (
                          <img src={rawUrl} alt='Raw Feed' className='max-h-[460px] w-full object-contain rounded' />
                        ) : (
                          <span className='font-sans text-xs text-muted-foreground'>Awaiting optical feed</span>
                        )}
                      </div>
                    </div>
                    <div className='flex flex-col space-y-1.5'>
                      <span className='text-[11px] font-sans text-primary font-semibold'>
                        Tactical Bounding Box & Target Overlay
                      </span>
                      <div className='flex-1 rounded-md overflow-hidden border border-primary/30 bg-black/50 flex items-center justify-center p-1'>
                        {annotUrl ? (
                          <img src={annotUrl} alt='Annotated' className='max-h-[460px] w-full object-contain rounded' />
                        ) : (
                          <span className='font-sans text-xs text-muted-foreground'>Execute detection to overlay boxes</span>
                        )}
                      </div>
                    </div>
                  </div>
                ) : activeView === 'raw' ? (
                  <div className='min-h-[420px] flex items-center justify-center bg-black/60 rounded-lg border border-border p-2'>
                    {rawUrl ? (
                      <img src={rawUrl} alt='Raw Optical Feed' className='max-h-[560px] w-full object-contain rounded' />
                    ) : (
                      <div className='text-center py-12 text-muted-foreground font-sans text-xs'>
                        No image loaded. Select a preset target or upload a custom image.
                      </div>
                    )}
                  </div>
                ) : (
                  <div className='min-h-[420px] flex items-center justify-center bg-black/60 rounded-lg border border-border p-2'>
                    {annotUrl ? (
                      <img src={annotUrl} alt='Annotated Bounding Boxes' className='max-h-[560px] w-full object-contain rounded' />
                    ) : rawUrl ? (
                      <img src={rawUrl} alt='Sensor Feed' className='max-h-[560px] w-full object-contain rounded' />
                    ) : (
                      <div className='text-center py-12 text-muted-foreground font-sans text-xs'>
                        No optical scan analyzed. Click "Execute Satellite Detection" to generate overlay.
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>

        {/* BOTTOM: Detected Vessels Telemetry Table */}
        {satelliteResult?.detections && satelliteResult.detections.length > 0 && (
          <Card className='bg-card/90 border-border'>
            <CardHeader className='pb-3 border-b border-border/50 flex flex-row items-center justify-between'>
              <div>
                <CardTitle className='text-xs font-sans font-semibold tracking-normal normal-case text-foreground'>
                  Target Bounding Box Coordinates & Telemetry Registry ({satelliteResult.detections.length} Vessels)
                </CardTitle>
                <p className='text-[11px] text-muted-foreground font-sans'>
                  Horizontal bounding box coordinates [x1, y1, x2, y2] extracted from 1024px feature maps
                </p>
              </div>
              <Badge variant='outline' className='font-sans text-xs text-primary border-red-500/40'>
                {satelliteResult.ship_count} TARGETS IDENTIFIED
              </Badge>
            </CardHeader>
            <CardContent className='p-0 overflow-x-auto'>
              <Table>
                <TableHeader>
                  <TableRow className='border-border/60 font-sans text-[11px] text-muted-foreground'>
                    <TableHead>Target ID</TableHead>
                    <TableHead>Confidence</TableHead>
                    <TableHead>Centroid (X, Y)</TableHead>
                    <TableHead>Bounding Box [x1, y1, x2, y2]</TableHead>
                    <TableHead>Width (px)</TableHead>
                    <TableHead>Height (px)</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody className='font-sans text-xs'>
                  {satelliteResult.detections.map((d, i) => {
                    const conf = d.confidence * 100
                    const bbox = d.bbox || [0, 0, 0, 0]
                    const width = (bbox[2] - bbox[0]).toFixed(1)
                    const height = (bbox[3] - bbox[1]).toFixed(1)
                    const cx = d.cx ?? (bbox[0] + bbox[2]) / 2
                    const cy = d.cy ?? (bbox[1] + bbox[3]) / 2

                    return (
                      <TableRow key={i} className='border-border/40 hover:bg-muted/40'>
                        <TableCell className='font-bold text-primary'>
                          Vessel #{String(i + 1).padStart(2, '0')}
                        </TableCell>
                        <TableCell>
                          <span
                            className={`px-1.5 py-0.5 rounded text-[11px] ${
                              conf >= 80
                                ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                                : conf >= 50
                                ? 'bg-red-500/15 text-primary border border-primary/30'
                                : 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                            }`}
                          >
                            {conf.toFixed(1)}%
                          </span>
                        </TableCell>
                        <TableCell className='text-muted-foreground'>
                          ({cx.toFixed(1)}, {cy.toFixed(1)})
                        </TableCell>
                        <TableCell className='text-foreground'>
                          [{bbox[0].toFixed(1)}, {bbox[1].toFixed(1)}, {bbox[2].toFixed(1)}, {bbox[3].toFixed(1)}]
                        </TableCell>
                        <TableCell className='text-muted-foreground'>{width} px</TableCell>
                        <TableCell className='text-muted-foreground'>{height} px</TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}
      </Main>
    </>
  )
}
