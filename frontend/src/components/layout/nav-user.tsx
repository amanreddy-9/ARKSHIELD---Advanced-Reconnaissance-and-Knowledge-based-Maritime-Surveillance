import { Link } from '@tanstack/react-router'
import {
  Activity,
  Cpu,
  Settings,
  Shield,
} from 'lucide-react'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from '@/components/ui/sidebar'
import { useSurveillanceStore } from '@/stores/surveillance-store'

type NavUserProps = {
  user?: {
    name?: string
    email?: string
  }
}

export function NavUser({ user }: NavUserProps) {
  const { backendOnline, pingMs } = useSurveillanceStore()

  const operatorName = user?.name || 'User'
  const callsign = user?.email || 'Local application'

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton
              size='lg'
              className='data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground border border-sidebar-border/60 rounded-md bg-sidebar-accent/30'
            >
              <Avatar className='h-8 w-8 rounded-md bg-primary/20 text-primary border border-primary/30 flex items-center justify-center'>
                <AvatarFallback className='rounded-md bg-primary/15 text-primary text-xs font-sans font-bold'>
                  OA
                </AvatarFallback>
              </Avatar>
              <div className='grid flex-1 text-start text-xs leading-tight overflow-hidden'>
                <span className='truncate font-semibold text-foreground flex items-center gap-1.5'>
                  {operatorName}
                  <span
                    className={`inline-block size-1.5 rounded-full ${
                      backendOnline ? 'bg-emerald-400' : 'bg-amber-400'
                    }`}
                  />
                </span>
                <span className='truncate font-sans text-[10px] text-muted-foreground'>
                  {backendOnline ? `ONLINE (${pingMs}ms)` : 'NODE STANDBY'}
                </span>
              </div>
            </SidebarMenuButton>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            className='w-56 rounded-lg bg-card border-border'
            side='top'
            align='end'
            sideOffset={4}
          >
            <DropdownMenuLabel className='p-0 font-normal'>
              <div className='flex items-center gap-2 px-2 py-1.5 text-left text-sm'>
                <div className='flex size-8 items-center justify-center rounded-md bg-primary/20 text-primary'>
                  <Shield className='size-4' />
                </div>
                <div className='grid flex-1 text-left text-xs leading-tight'>
                  <span className='truncate font-semibold'>{operatorName}</span>
                  <span className='truncate font-sans text-[10px] text-muted-foreground'>{callsign}</span>
                </div>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuGroup>
              <DropdownMenuItem asChild>
                <Link to='/health' className='flex items-center gap-2 text-xs'>
                  <Activity className='size-3.5 text-primary' />
                  <span>Subsystem Telemetry</span>
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link to='/ppo' className='flex items-center gap-2 text-xs'>
                  <Cpu className='size-3.5 text-primary' />
                  <span>Edge Compute Engine</span>
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link to='/settings' className='flex items-center gap-2 text-xs'>
                  <Settings className='size-3.5 text-primary' />
                  <span>System Settings</span>
                </Link>
              </DropdownMenuItem>
            </DropdownMenuGroup>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  )
}
