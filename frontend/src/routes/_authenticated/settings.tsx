import { createFileRoute } from '@tanstack/react-router'
import { SettingsFeature } from '@/features/settings'

export const Route = createFileRoute('/_authenticated/settings')({
  component: SettingsFeature,
})
