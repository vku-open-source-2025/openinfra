import * as React from "react"
import { cn } from "../../lib/utils"
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from "lucide-react"

export type ToastType = "success" | "error" | "info" | "warning"

export interface Toast {
  id: string
  title?: string
  description?: string
  type?: ToastType
  duration?: number
}

export interface ToastProps extends Toast {
  onClose: () => void
}

const ToastComponent: React.FC<ToastProps> = ({
  id,
  title,
  description,
  type = "info",
  onClose,
}) => {
  const icons = {
    success: CheckCircle,
    error: AlertCircle,
    info: Info,
    warning: AlertTriangle,
  }

  const colors = {
    success: "bg-green-50 border-green-200 text-green-900",
    error: "bg-red-50 border-red-200 text-red-900",
    info: "bg-blue-50 border-blue-200 text-blue-900",
    warning: "bg-amber-50 border-amber-200 text-amber-900",
  }

  const Icon = icons[type]

  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-lg border p-4 shadow-lg",
        colors[type]
      )}
    >
      <Icon className="h-5 w-5 shrink-0 mt-0.5" />
      <div className="flex-1">
        {title && <div className="font-semibold text-sm">{title}</div>}
        {description && <div className="text-sm mt-1">{description}</div>}
      </div>
      <button
        onClick={onClose}
        className="shrink-0 rounded-sm opacity-70 hover:opacity-100"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  )
}

export interface ToastContainerProps {
  toasts: Toast[]
  onRemove: (id: string) => void
}

export const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, onRemove }) => {
  if (toasts.length === 0) return null

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-md">
      {toasts.map((toast) => (
        <ToastComponent key={toast.id} {...toast} onClose={() => onRemove(toast.id)} />
      ))}
    </div>
  )
}

// Toast hook for managing toasts
export const useToast = () => {
  const [toasts, setToasts] = React.useState<Toast[]>([])

  const addToast = React.useCallback(
    (toast: Omit<Toast, "id">) => {
      const id = Math.random().toString(36).substring(7)
      const newToast = { ...toast, id, duration: toast.duration || 5000 }
      setToasts((prev) => [...prev, newToast])

      if (newToast.duration && newToast.duration > 0) {
        setTimeout(() => {
          removeToast(id)
        }, newToast.duration)
      }
    },
    []
  )

  const removeToast = React.useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id))
  }, [])

  return {
    toasts,
    addToast,
    removeToast,
    success: (title: string, description?: string) =>
      addToast({ title, description, type: "success" }),
    error: (title: string, description?: string) =>
      addToast({ title, description, type: "error" }),
    info: (title: string, description?: string) =>
      addToast({ title, description, type: "info" }),
    warning: (title: string, description?: string) =>
      addToast({ title, description, type: "warning" }),
  }
}

export { ToastComponent as Toast }
