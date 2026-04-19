import { createFileRoute } from '@tanstack/react-router'
import EmergencyCenter from '@/pages/emergency/EmergencyCenter'

export const Route = createFileRoute('/admin/emergency-center')({
  component: EmergencyCenter,
})
