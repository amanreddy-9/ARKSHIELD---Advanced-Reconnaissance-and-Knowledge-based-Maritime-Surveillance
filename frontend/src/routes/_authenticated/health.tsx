import { createFileRoute } from '@tanstack/react-router'
import { HealthFeature } from '@/features/health'

export const Route = createFileRoute('/_authenticated/health')({
  component: HealthFeature,
})
