import { useState } from 'react'
import {
  Bot,
  BrainCircuit,
  Compass,
  FileText,
  Loader2,
  Send,
  Sparkles,
  User,
} from 'lucide-react'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { sendChatMessage } from '@/api/intelligence'
import { useSurveillanceStore } from '@/stores/surveillance-store'

export function IntelligenceFeature() {
  const {
    satelliteResult,
    droneResult,
    chatHistory,
    addChatMessage,
  } = useSurveillanceStore()

  const [inputMessage, setInputMessage] = useState<string>('')
  const [loading, setLoading] = useState<boolean>(false)

  // Construct current session tactical context
  const buildCurrentContext = () => {
    let ctx = ''
    if (satelliteResult) {
      ctx += `SATELLITE SURVEILLANCE RUN:\n${JSON.stringify({
        ship_count: satelliteResult.ship_count,
        model: satelliteResult.model_variant,
        weights: satelliteResult.weights_used,
        detections: satelliteResult.detections,
        vlm_analysis: satelliteResult.vlm_analysis,
      })}\n\n`
    }
    if (droneResult) {
      const summary = {
        primary_vessel: droneResult.primary_vessel,
        unique_track_count: droneResult.unique_track_count,
        processed_frames: droneResult.processed_frames,
        scan_mode: droneResult.scan_mode,
        estimated_compute_reduction: droneResult.estimated_compute_reduction,
        processing_mode_counts: droneResult.processing_mode_counts,
        track_summaries: droneResult.track_summaries,
      }
      ctx += `DRONE VIDEO SURVEILLANCE RUN:\n${JSON.stringify(summary)}\n\n`
    }
    return ctx
  }

  const handleSendMessage = async (queryText?: string) => {
    const textToSend = queryText || inputMessage
    if (!textToSend.trim() || loading) return

    const userMsg = { role: 'user' as const, content: textToSend.trim() }
    addChatMessage(userMsg)
    setInputMessage('')
    setLoading(true)

    try {
      const ctx = buildCurrentContext()
      const resp = await sendChatMessage(textToSend, chatHistory, ctx)
      addChatMessage({
        role: 'assistant',
        content: resp.reply || 'No intelligence synthesized.',
      })
    } catch (err: any) {
      addChatMessage({
        role: 'assistant',
        content: `Tactical Intelligence Error: ${err?.message || 'Failed to reach AI service'}. Ensure FastAPI backend is online.`,
      })
    } finally {
      setLoading(false)
    }
  }

  const vlmSatBriefing = typeof satelliteResult?.vlm_analysis === 'string'
    ? satelliteResult.vlm_analysis
    : (satelliteResult?.vlm_analysis as any)?.text || (satelliteResult?.vlm_analysis as any)?.briefing || null

  return (
    <>
      <Header fixed>
        <div className='flex items-center gap-2'>
          <Bot className='size-5 text-primary' />
          <div>
            <h1 className='text-sm font-bold tracking-normal font-sans text-foreground normal-case'>
              Tactical VLM Intelligence Analyst Workstation
            </h1>
            <p className='text-[10px] font-sans text-muted-foreground'>
              Groq Qwen-2.5 Vision / 70B Multimodal Reasoning Engine
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
        {/* Analyst Workstation Grid */}
        <div className='grid grid-cols-1 lg:grid-cols-12 gap-4'>
          {/* LEFT: Context Summary & Mission Briefing (5 cols) */}
          <div className='lg:col-span-5 space-y-4'>
            {/* Mission Briefing Card */}
            <Card className='bg-card/90 border-border'>
              <CardHeader className='pb-3 border-b border-border/50'>
                <CardTitle className='text-xs font-sans font-semibold tracking-normal normal-case text-foreground flex items-center gap-2'>
                  <FileText className='size-4 text-primary' />
                  Automated Maritime Briefing Report
                </CardTitle>
                <p className='text-[11px] text-muted-foreground font-sans'>
                  Synthesized from wide-area optical imagery and track history
                </p>
              </CardHeader>
              <CardContent className='p-4 text-xs font-sans leading-relaxed text-muted-foreground'>
                {vlmSatBriefing ? (
                  <div className='p-3.5 rounded-md bg-secondary/40 border border-primary/20 text-foreground whitespace-pre-line'>
                    <p className='font-bold text-primary mb-1 text-[11px] normal-case tracking-normal'>
                      OATICAL INTELLIGENCE ASSESSMENT:
                    </p>
                    {typeof satelliteResult?.vlm_analysis === 'object' && (
                      <span className='block text-xs text-muted-foreground mb-2'>
                        VLM: {satelliteResult.vlm_analysis.status === 'OK'
                          ? satelliteResult.vlm_analysis.source || 'fresh'
                          : 'unavailable'}
                      </span>
                    )}
                    {vlmSatBriefing}
                  </div>
                ) : (
                  <div className='p-6 text-center text-muted-foreground'>
                    No briefing available yet. Execute Satellite Detection to generate an automated mission assessment report.
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Tactical Context Telemetry */}
            <Card className='bg-card/90 border-border'>
              <CardHeader className='pb-3 border-b border-border/50'>
                <CardTitle className='text-xs font-sans font-semibold tracking-normal normal-case text-foreground flex items-center gap-2'>
                  <Compass className='size-4 text-primary' />
                  Injected Session Telemetry Context
                </CardTitle>
              </CardHeader>
              <CardContent className='p-4 font-sans text-xs space-y-2 text-muted-foreground'>
                <div className='flex justify-between'>
                  <span>Satellite Vessels:</span>
                  <span className='font-bold text-primary'>{satelliteResult?.ship_count ?? 0}</span>
                </div>
                <div className='flex justify-between'>
                  <span>Primary Target:</span>
                  <span className='font-bold text-emerald-400'>{droneResult?.primary_vessel?.label || 'None'}</span>
                </div>
                <div className='flex justify-between'>
                  <span>Target Stability:</span>
                  <span>{droneResult?.primary_vessel ? `${(droneResult.primary_vessel.stability * 100).toFixed(1)}%` : 'N/A'}</span>
                </div>
                <div className='flex justify-between'>
                  <span>Adaptive Mode:</span>
                  <span>{droneResult?.scan_mode || 'Standby'}</span>
                </div>
                <div className='flex justify-between'>
                  <span>PPO Compute Conserved:</span>
                  <span className='text-amber-400'>{droneResult?.estimated_compute_reduction?.toFixed(1) || 0}%</span>
                </div>
              </CardContent>
            </Card>

            {/* Query Shortcuts */}
            <Card className='bg-card/90 border-border'>
              <CardHeader className='pb-2 border-b border-border/50'>
                <CardTitle className='text-xs font-sans font-semibold tracking-normal normal-case text-foreground flex items-center gap-2'>
                  <Sparkles className='size-4 text-primary' />
                  Tactical Query Shortcuts
                </CardTitle>
              </CardHeader>
              <CardContent className='p-3 space-y-2'>
                <Button
                  size='sm'
                  variant='outline'
                  onClick={() => handleSendMessage('Summarize all detected vessels and their bounding box coordinates from the current surveillance session.')}
                  disabled={loading}
                  className='w-full text-start justify-start font-sans text-xs h-auto py-2 px-3 border-border/60 hover:border-primary/50'
                >
                  📋 Summarize all detected vessels & coordinates
                </Button>
                <Button
                  size='sm'
                  variant='outline'
                  onClick={() => handleSendMessage('What is the primary vessel identified, its assigned Track ID, and its temporal classification stability?')}
                  disabled={loading}
                  className='w-full text-start justify-start font-sans text-xs h-auto py-2 px-3 border-border/60 hover:border-primary/50'
                >
                  🚢 Explain primary vessel tracking & stability
                </Button>
                <Button
                  size='sm'
                  variant='outline'
                  onClick={() => handleSendMessage('Explain how the PPO adaptive scheduler throttled compute during the mission and the estimated compute reduction achieved.')}
                  disabled={loading}
                  className='w-full text-start justify-start font-sans text-xs h-auto py-2 px-3 border-border/60 hover:border-primary/50'
                >
                  ⚡ Detail PPO adaptive compute savings
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* RIGHT: Analyst Inquiry Terminal (7 cols) */}
          <div className='lg:col-span-7 flex flex-col'>
            <Card className='bg-card/90 border-border flex-1 flex flex-col h-[650px]'>
              <CardHeader className='pb-3 border-b border-border/50 flex flex-row items-center justify-between'>
                <div className='flex items-center gap-2'>
                  <BrainCircuit className='size-4 text-primary' />
                  <CardTitle className='text-xs font-sans font-semibold tracking-normal normal-case text-foreground'>
                    Analyst Tactical Conversation Log
                  </CardTitle>
                </div>
                <Badge variant='outline' className='font-sans text-xs border-primary/40 text-primary'>
                  QWEN-2.5-32B VISION
                </Badge>
              </CardHeader>
              <CardContent className='flex-1 p-4 flex flex-col justify-between overflow-hidden'>
                {/* Messages stream */}
                <ScrollArea className='flex-1 pe-3 pr-2'>
                  <div className='space-y-3.5'>
                    {chatHistory.map((msg, idx) => {
                      const isUser = msg.role === 'user'
                      return (
                        <div
                          key={idx}
                          className={`flex items-start gap-2.5 ${
                            isUser ? 'flex-row-reverse' : ''
                          }`}
                        >
                          <div
                            className={`size-7 rounded-md shrink-0 flex items-center justify-center ${
                              isUser
                                ? 'bg-primary/20 text-primary border border-primary/40'
                                : 'bg-red-500/15 text-primary border border-red-500/40'
                            }`}
                          >
                            {isUser ? <User className='size-4' /> : <Bot className='size-4' />}
                          </div>
                          <div
                            className={`p-3 rounded-lg max-w-[85%] font-sans text-xs leading-relaxed whitespace-pre-line ${
                              isUser
                                ? 'bg-primary text-primary-foreground font-sans'
                                : 'bg-secondary/60 text-foreground border border-border/80'
                            }`}
                          >
                            {msg.content}
                          </div>
                        </div>
                      )
                    })}
                    {loading && (
                      <div className='flex items-center gap-2 text-xs font-sans text-muted-foreground p-3 bg-secondary/30 rounded-lg'>
                        <Loader2 className='size-3.5 animate-spin text-primary' />
                        <span>Synthesizing maritime intelligence with Groq Qwen-2.5...</span>
                      </div>
                    )}
                  </div>
                </ScrollArea>

                {/* Input box */}
                <div className='pt-3 mt-2 border-t border-border/50 flex gap-2'>
                  <Input
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleSendMessage()
                    }}
                    placeholder='Inquire about target telemetry, coordinates, or compute savings...'
                    disabled={loading}
                    className='font-sans text-xs bg-secondary/40'
                  />
                  <Button
                    onClick={() => handleSendMessage()}
                    disabled={loading || !inputMessage.trim()}
                    className='font-sans text-xs bg-primary text-primary-foreground hover:bg-primary/90 px-4'
                  >
                    <Send className='size-3.5' />
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </Main>
    </>
  )
}
