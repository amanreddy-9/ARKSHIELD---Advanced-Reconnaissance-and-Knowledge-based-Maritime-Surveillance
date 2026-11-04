import { createFileRoute } from '@tanstack/react-router'
import { OperationsFeature } from '@/features/operations'

export const Route = createFileRoute('/_authenticated/operations')({
  component: OperationsFeature,
})
