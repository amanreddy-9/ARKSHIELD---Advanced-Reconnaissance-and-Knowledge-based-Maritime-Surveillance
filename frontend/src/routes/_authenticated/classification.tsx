import { createFileRoute } from '@tanstack/react-router'
import { ClassificationFeature } from '@/features/classification'

export const Route = createFileRoute('/_authenticated/classification')({
  component: ClassificationFeature,
})
