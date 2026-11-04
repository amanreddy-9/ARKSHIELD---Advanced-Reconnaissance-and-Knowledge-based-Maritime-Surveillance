import { useState } from 'react'
import {
  Check,
  Globe,
  RefreshCw,
  Save,
  Server,
  Settings as SettingsIcon,
} from 'lucide-react'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { checkBasicHealth } from '@/api/health'
import { getApiBaseUrl, setApiBaseUrl } from '@/api/client'
import { useSurveillanceStore } from '@/stores/surveillance-store'

export function SettingsFeature() {
  const { setSystemStatus } = useSurveillanceStore()
  const [apiUrl, setApiUrl] = useState<string>(getApiBaseUrl())
  const [testResult, setTestResult] = useState<string | null>(null)
  const [testing, setTesting] = useState<boolean>(false)
  const [saved, setSaved] = useState<boolean>(false)

  const handleSave = () => {
    setApiBaseUrl(apiUrl)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const handleTestConnection = async () => {
    setTesting(true)
    setTestResult(null)
    setApiBaseUrl(apiUrl)
    try {
      const res = await checkBasicHealth()
      setTestResult(`Connected successfully: ${res.project} (${res.ping_ms} ms)`)
      setSystemStatus(true, res.ping_ms)
    } catch (err: any) {
      setTestResult(`Connection failed: ${err.message}`)
      setSystemStatus(false, 0)
    } finally {
      setTesting(false)
    }
  }

  return (
    <>
      <Header fixed>
        <div className='flex items-center gap-2'>
          <SettingsIcon className='size-5 text-primary' />
          <div>
            <h1 className='text-sm font-bold tracking-normal font-sans text-foreground normal-case'>
              Command Center Configuration
            </h1>
            <p className='text-[10px] font-sans text-muted-foreground'>
              FastAPI Node Endpoint & Maritime Surveillance Inference Preferences
            </p>
          </div>
        </div>
        <div className='ms-auto flex items-center space-x-2'>
          <Search />
          <ThemeSwitch />
          <ProfileDropdown />
        </div>
      </Header>

      <Main className='space-y-4 p-4 md:p-6 max-w-4xl'>
        {/* Backend API Configuration */}
        <Card className='bg-card/90 border-border'>
          <CardHeader className='pb-3 border-b border-border/50'>
            <CardTitle className='text-xs font-sans font-semibold tracking-normal normal-case text-foreground flex items-center gap-2'>
              <Server className='size-4 text-primary' />
              FastAPI Backend Endpoint URL
            </CardTitle>
            <p className='text-[11px] text-muted-foreground font-sans'>
              Configure the network URL of the Python FastAPI deep learning backend
            </p>
          </CardHeader>
          <CardContent className='p-4 space-y-4 font-sans text-xs'>
            <div className='space-y-1.5'>
              <Label className='text-muted-foreground'>Backend Base URL:</Label>
              <div className='flex gap-2'>
                <Input
                  value={apiUrl}
                  onChange={(e) => setApiUrl(e.target.value)}
                  placeholder='http://127.0.0.1:8000'
                  className='font-sans text-xs bg-secondary/40'
                />
                <Button
                  onClick={handleSave}
                  className='font-sans text-xs bg-primary text-primary-foreground hover:bg-primary/90'
                >
                  {saved ? (
                    <>
                      <Check className='size-3.5 mr-1.5 text-emerald-400' /> Saved
                    </>
                  ) : (
                    <>
                      <Save className='size-3.5 mr-1.5' /> Save
                    </>
                  )}
                </Button>
                <Button
                  variant='outline'
                  onClick={handleTestConnection}
                  disabled={testing}
                  className='font-sans text-xs border-primary/40 text-primary'
                >
                  <RefreshCw className={`size-3.5 mr-1.5 ${testing ? 'animate-spin' : ''}`} />
                  Ping Node
                </Button>
              </div>
            </div>

            {testResult && (
              <div
                className={`p-3 rounded-md text-xs font-sans ${
                  testResult.includes('successfully')
                    ? 'bg-emerald-500/15 border border-emerald-500/30 text-emerald-400'
                    : 'bg-destructive/15 border border-destructive/30 text-destructive'
                }`}
              >
                {testResult}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Pipeline Information */}
        <Card className='bg-card/90 border-border'>
          <CardHeader className='pb-3 border-b border-border/50'>
            <CardTitle className='text-xs font-sans font-semibold tracking-normal normal-case text-foreground flex items-center gap-2'>
              <Globe className='size-4 text-primary' />
              Active System Architecture Information
            </CardTitle>
          </CardHeader>
          <CardContent className='p-4 font-sans text-xs space-y-2 text-muted-foreground'>
            <div className='flex justify-between py-1 border-b border-border/40'>
              <span>Frontend Architecture:</span>
              <span className='text-foreground'>React 19 + Vite 8 + TypeScript</span>
            </div>
            <div className='flex justify-between py-1 border-b border-border/40'>
              <span>UI Framework:</span>
              <span className='text-foreground'>shadcn/ui + Tailwind CSS 4</span>
            </div>
            <div className='flex justify-between py-1 border-b border-border/40'>
              <span>Detector Resolution:</span>
              <span className='text-primary font-bold'>1024 × 1024 High-Res Feature Preserving</span>
            </div>
            <div className='flex justify-between py-1 border-b border-border/40'>
              <span>Tracker Mathematics:</span>
              <span className='text-emerald-400 font-bold'>Continuous 8-State Kalman + 4-Feature Cost</span>
            </div>
            <div className='flex justify-between py-1 border-b border-border/40'>
              <span>RL Agent Engine:</span>
              <span className='text-amber-400 font-bold'>Gymnasium PPO Policy + Safety Override Layer</span>
            </div>
            <div className='flex justify-between py-1'>
              <span>Vision-Language Reasoning:</span>
              <span className='text-primary font-bold'>Groq Qwen-2.5 Vision / 70B Multimodal</span>
            </div>
          </CardContent>
        </Card>
      </Main>
    </>
  )
}
