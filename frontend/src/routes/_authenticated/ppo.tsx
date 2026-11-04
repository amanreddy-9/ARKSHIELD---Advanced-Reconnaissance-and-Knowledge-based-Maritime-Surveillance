import { createFileRoute } from '@tanstack/react-router'
import { PpoFeature } from '@/features/ppo'

export const Route = createFileRoute('/_authenticated/ppo')({
  component: PpoFeature,
})
