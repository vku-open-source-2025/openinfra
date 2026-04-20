import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/admin/emergency-center/during')({
  component: RouteComponent,
})

function RouteComponent() {
  return <div>Hello "/admin/emergency-center/during"!</div>
}
