import {
  ArrowRight,
  Bot,
  Cpu,
  Radio,
  Satellite,
  Shield,
  Ship,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

const STAGES = [
  {
    step: '01',
    title: 'Wide-Area Satellite',
    model: 'YOLO11n-VHRV @ 1024px',
    desc: 'High-res optical sensor scanning without small-ship downsampling loss',
    metric: '94.6% mAP50',
    icon: Satellite,
    color: 'text-primary',
    border: 'border-primary/30',
    badge: 'Wide-Area Scan',
  },
  {
    step: '02',
    title: 'Tactical UAV Handoff',
    model: 'Drone Video Feed (MP4/AVI)',
    desc: 'Close-quarters surveillance targeting handoff coordinates from orbit',
    metric: 'Real-time Feed',
    icon: Radio,
    color: 'text-primary',
    border: 'border-primary/30',
    badge: 'Target Lock',
  },
  {
    step: '03',
    title: 'Continuous Tracking',
    model: '8-State Kalman Tracker',
    desc: 'Multi-feature cost: IoU + centroid proximity + aspect ratio + motion vector',
    metric: '3-stage Hungarian',
    icon: Shield,
    color: 'text-emerald-400',
    border: 'border-emerald-500/30',
    badge: 'Multi-Ship Tracking',
  },
  {
    step: '04',
    title: 'Vessel Classification',
    model: 'ConvNeXt-Tiny (FGS-10)',
    desc: '10-class fine-grained maritime identification with temporal evidence voting',
    metric: '92.3% Top-1 Acc',
    icon: Ship,
    color: 'text-primary',
    border: 'border-primary/30',
    badge: 'Temporal Stability',
  },
  {
    step: '05',
    title: 'Adaptive Compute',
    model: 'Gymnasium + SB3 PPO',
    desc: 'Dynamic inference throttling (LOW 1/4, NORM 1/2, HIGH 1/1) + Safety Override',
    metric: '45-75% Savings',
    icon: Cpu,
    color: 'text-amber-400',
    border: 'border-amber-500/30',
    badge: 'RL Edge Proxy',
  },
  {
    step: '06',
    title: 'Tactical VLM Briefing',
    model: 'Groq Qwen-2.5 Vision / 70B',
    desc: 'Automated multimodal maritime intelligence synthesis and natural language report',
    metric: 'Zero-Shot Reasoning',
    icon: Bot,
    color: 'text-primary',
    border: 'border-primary/30',
    badge: 'Mission Briefing',
  },
]

export function PipelineFlow() {
  return (
    <Card className='bg-card/90 border-border'>
      <CardHeader className='pb-3 border-b border-border/60'>
        <div className='flex items-center justify-between'>
          <div>
            <CardTitle className='text-sm font-semibold tracking-normal normal-case text-foreground flex items-center gap-2 font-sans'>
              <Shield className='size-4 text-primary' />
              Autonomous Surveillance Architecture Pipeline
            </CardTitle>
            <p className='text-xs text-muted-foreground mt-0.5'>
              Multi-tiered perception and reasoning pipeline linking satellite detection to tactical UAV edge compute and VLM briefings
            </p>
          </div>
          <Badge variant='outline' className='font-sans text-[10px] border-primary/40 text-primary'>
            END-TO-END PIPELINE
          </Badge>
        </div>
      </CardHeader>
      <CardContent className='p-4 pt-5'>
        <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-3'>
          {STAGES.map((s, idx) => {
            const Icon = s.icon
            return (
              <div key={s.step} className='relative group'>
                <div
                  className={`h-full flex flex-col justify-between p-3.5 rounded-lg bg-card/60 border ${s.border} transition-all duration-200 hover:bg-card hover:border-primary/60`}
                >
                  <div>
                    <div className='flex items-center justify-between mb-2'>
                      <span className='font-sans text-[10px] font-bold text-muted-foreground'>
                        STAGE {s.step}
                      </span>
                      <Icon className={`size-4 ${s.color}`} />
                    </div>
                    <h4 className='text-xs font-semibold text-foreground tracking-tight'>
                      {s.title}
                    </h4>
                    <p className='text-[10px] font-sans text-primary font-medium mt-0.5'>
                      {s.model}
                    </p>
                    <p className='text-[11px] text-muted-foreground leading-snug mt-1.5'>
                      {s.desc}
                    </p>
                  </div>
                  <div className='mt-3 pt-2 border-t border-border/40 flex items-center justify-between'>
                    <span className='text-[10px] font-sans text-emerald-400 font-semibold'>
                      {s.metric}
                    </span>
                    <span className='text-[9px] font-sans text-muted-foreground/80 px-1.5 py-0.5 rounded bg-muted'>
                      {s.badge}
                    </span>
                  </div>
                </div>

                {/* Arrow connector between stages on desktop */}
                {idx < STAGES.length - 1 && (
                  <div className='hidden lg:block absolute -right-2 top-1/2 -translate-y-1/2 z-10 pointer-events-none text-muted-foreground/40'>
                    <ArrowRight className='size-3.5' />
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
