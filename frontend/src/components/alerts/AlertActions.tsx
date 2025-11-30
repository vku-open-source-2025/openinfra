import { Button } from "../ui/button"
import type { Alert } from "../../types/alert"
import { CheckCircle, X, Check } from "lucide-react"
import { Textarea } from "../ui/textarea"
import { useState } from "react"

interface AlertActionsProps {
  alert: Alert
  onAcknowledge: () => Promise<void>
  onResolve: (notes?: string) => Promise<void>
  onDismiss: () => Promise<void>
  canAcknowledge?: boolean
  canResolve?: boolean
  canDismiss?: boolean
}

export const AlertActions: React.FC<AlertActionsProps> = ({
  alert,
  onAcknowledge,
  onResolve,
  onDismiss,
  canAcknowledge = false,
  canResolve = false,
  canDismiss = false,
}) => {
  const [resolutionNotes, setResolutionNotes] = useState("")
  const [isProcessing, setIsProcessing] = useState(false)
  const [showResolveForm, setShowResolveForm] = useState(false)

  const handleAcknowledge = async () => {
    setIsProcessing(true)
    try {
      await onAcknowledge()
    } finally {
      setIsProcessing(false)
    }
  }

  const handleResolve = async () => {
    setIsProcessing(true)
    try {
      await onResolve(resolutionNotes || undefined)
      setResolutionNotes("")
      setShowResolveForm(false)
    } finally {
      setIsProcessing(false)
    }
  }

  const handleDismiss = async () => {
    setIsProcessing(true)
    try {
      await onDismiss()
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="space-y-2">
      {alert.status === "active" && canAcknowledge && (
        <Button onClick={handleAcknowledge} disabled={isProcessing} className="w-full" size="sm">
          <CheckCircle className="h-4 w-4 mr-2" />
          Acknowledge
        </Button>
      )}

      {alert.status === "active" && canResolve && !showResolveForm && (
        <Button
          onClick={() => setShowResolveForm(true)}
          disabled={isProcessing}
          className="w-full"
          size="sm"
          variant="outline"
        >
          <Check className="h-4 w-4 mr-2" />
          Resolve
        </Button>
      )}

      {showResolveForm && (
        <div className="space-y-2">
          <Textarea
            value={resolutionNotes}
            onChange={(e) => setResolutionNotes(e.target.value)}
            placeholder="Resolution notes (optional)..."
            rows={2}
            className="text-sm"
          />
          <div className="flex gap-2">
            <Button onClick={handleResolve} disabled={isProcessing} size="sm" className="flex-1">
              Confirm Resolve
            </Button>
            <Button
              onClick={() => {
                setShowResolveForm(false)
                setResolutionNotes("")
              }}
              variant="outline"
              size="sm"
            >
              Cancel
            </Button>
          </div>
        </div>
      )}

      {alert.status === "active" && canDismiss && (
        <Button onClick={handleDismiss} disabled={isProcessing} className="w-full" size="sm" variant="outline">
          <X className="h-4 w-4 mr-2" />
          Dismiss
        </Button>
      )}
    </div>
  )
}
