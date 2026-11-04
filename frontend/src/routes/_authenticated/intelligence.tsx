import { createFileRoute } from '@tanstack/react-router'
import { IntelligenceFeature } from '@/features/intelligence'

export const Route = createFileRoute('/_authenticated/intelligence')({
  component: IntelligenceFeature,
})
