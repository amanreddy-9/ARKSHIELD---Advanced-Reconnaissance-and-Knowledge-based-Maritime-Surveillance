import { createFileRoute } from '@tanstack/react-router'
import { SatelliteFeature } from '@/features/satellite'

export const Route = createFileRoute('/_authenticated/satellite')({
  component: SatelliteFeature,
})
