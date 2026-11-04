import { createFileRoute } from '@tanstack/react-router'
import { DiagnosticsFeature } from '@/features/diagnostics'

export const Route = createFileRoute('/_authenticated/diagnostics')({
  component: DiagnosticsFeature,
})
