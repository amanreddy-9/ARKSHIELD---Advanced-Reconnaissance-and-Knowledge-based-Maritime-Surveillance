import { createFileRoute } from '@tanstack/react-router'
import { TrackingFeature } from '@/features/tracking'

export const Route = createFileRoute('/_authenticated/tracking')({
  component: TrackingFeature,
})
