import {
  Bot,
  Compass,
  Cpu,
  Gauge,
  LayoutDashboard,
  Microscope,
  Radio,
  Satellite,
  Server,
  Settings,
  Ship,
} from 'lucide-react'
import { type SidebarData } from '../types'

export const sidebarData: SidebarData = {
  user: {
    name: 'User',
    email: 'RTX-3050 CUDA 12.6',
    avatar: '',
  },
  teams: [
    {
      name: 'OATrack-VLM',
      logo: Compass,
      plan: 'Maritime Intelligence',
    },
  ],
  navGroups: [
    {
      title: 'Overview',
      items: [
        {
          title: 'Overview',
          url: '/',
          icon: LayoutDashboard,
        },
        {
          title: 'Results',
          url: '/operations',
          icon: Compass,
        },
      ],
    },
    {
      title: 'SURVEILLANCE',
      items: [
        {
          title: 'Satellite Detection',
          url: '/satellite',
          icon: Satellite,
        },
        {
          title: 'Video tracking',
          url: '/tracking',
          icon: Radio,
        },
      ],
    },
    {
      title: 'AI SYSTEMS',
      items: [
        {
          title: 'Vessel Classification',
          url: '/classification',
          icon: Ship,
        },
        {
          title: 'PPO Compute',
          url: '/ppo',
          icon: Cpu,
        },
        {
          title: 'VLM Intelligence',
          url: '/intelligence',
          icon: Bot,
        },
      ],
    },
    {
      title: 'ANALYTICS',
      items: [
        {
          title: 'Performance',
          url: '/performance',
          icon: Gauge,
        },
        {
          title: 'Diagnostics',
          url: '/diagnostics',
          icon: Microscope,
        },
      ],
    },
    {
      title: 'SYSTEM',
      items: [
        {
          title: 'System Health',
          url: '/health',
          icon: Server,
        },
        {
          title: 'Settings',
          url: '/settings',
          icon: Settings,
        },
      ],
    },
  ],
}
