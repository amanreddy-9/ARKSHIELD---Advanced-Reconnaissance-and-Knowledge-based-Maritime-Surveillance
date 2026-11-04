import { Link } from '@tanstack/react-router'
import { Anchor, Menu, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from '@/components/ui/sidebar'
import { Button } from '../ui/button'

export function AppTitle() {
  const { setOpenMobile } = useSidebar()
  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <SidebarMenuButton
          size='lg'
          className='gap-2 py-2 hover:bg-sidebar-accent/50 active:bg-sidebar-accent/50'
          asChild
        >
          <div className='flex items-center justify-between w-full'>
            <Link
              to='/'
              onClick={() => setOpenMobile(false)}
              className='flex items-center gap-2.5 text-start leading-tight overflow-hidden'
            >
              <div className='flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary/15 border border-primary/40 text-primary shadow-sm'>
                <Anchor className='size-5 text-primary stroke-[2.2]' />
              </div>
              <div className='grid flex-1 overflow-hidden'>
                <span className='truncate font-bold tracking-normal text-foreground text-sm font-sans'>
                  OATrack-VLM
                </span>
                <span className='truncate text-[10px] text-muted-foreground font-sans'>
                  Maritime Intelligence
                </span>
              </div>
            </Link>
            <ToggleSidebar />
          </div>
        </SidebarMenuButton>
      </SidebarMenuItem>
    </SidebarMenu>
  )
}

function ToggleSidebar({
  className,
  onClick,
  ...props
}: React.ComponentProps<typeof Button>) {
  const { toggleSidebar } = useSidebar()

  return (
    <Button
      data-sidebar='trigger'
      data-slot='sidebar-trigger'
      variant='ghost'
      size='icon'
      className={cn('aspect-square size-8 shrink-0 text-muted-foreground hover:text-foreground', className)}
      onClick={(event) => {
        onClick?.(event)
        toggleSidebar()
      }}
      {...props}
    >
      <X className='md:hidden size-4' />
      <Menu className='max-md:hidden size-4' />
      <span className='sr-only'>Toggle Sidebar</span>
    </Button>
  )
}
