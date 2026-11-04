import { createFileRoute } from '@tanstack/react-router'
import { PerformanceFeature } from '@/features/performance'

export const Route = createFileRoute('/_authenticated/performance')({
  component: PerformanceFeature,
})
