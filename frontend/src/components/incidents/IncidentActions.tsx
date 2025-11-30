import { Button } from "../ui/button"
import { Select } from "../ui/select"
import type { Incident, IncidentStatus } from "../../types/incident"
import { CheckCircle, User, Wrench, X } from "lucide-react"
import { useState } from "react"

interface IncidentActionsProps {
  incident: Incident
  onAcknowledge: () => Promise<void>
  onAssign: (userId: string) => Promise<void>
  onResolve: (notes: string, type: "fixed" | "duplicate" | "invalid" | "deferred") => Promise<void>
  availableUsers?: Array<{ id: string; full_name: string }>
  canAcknowledge?: boolean
  canAssign?: boolean
  canResolve?: boolean
}

export const IncidentActions: React.FC<IncidentActionsProps> = ({
  incident,
  onAcknowledge,
  onAssign,
  onResolve,
  availableUsers = [],
  canAcknowledge = false,
  canAssign = false,
  canResolve = false,
}) => {
  const [selectedUserId, setSelectedUserId] = useState("")
  const [resolutionNotes, setResolutionNotes] = useState("")
  const [resolutionType, setResolutionType] = useState<"fixed" | "duplicate" | "invalid" | "deferred">("fixed")
  const [isProcessing, setIsProcessing] = useState(false)

  const handleAcknowledge = async () => {
    setIsProcessing(true)
    try {
      await onAcknowledge()
    } finally {
      setIsProcessing(false)
    }
  }

  const handleAssign = async () => {
    if (!selectedUserId) return
    setIsProcessing(true)
    try {
      await onAssign(selectedUserId)
      setSelectedUserId("")
    } finally {
      setIsProcessing(false)
    }
  }

  const handleResolve = async () => {
    if (!resolutionNotes.trim()) return
    setIsProcessing(true)
    try {
      await onResolve(resolutionNotes, resolutionType)
      setResolutionNotes("")
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="space-y-4">
      {incident.status === "reported" && canAcknowledge && (
        <Button onClick={handleAcknowledge} disabled={isProcessing} className="w-full">
          <CheckCircle className="h-4 w-4 mr-2" />
          Acknowledge Incident
        </Button>
      )}

      {incident.status === "acknowledged" && canAssign && (
        <div className="space-y-2">
          <Select
            value={selectedUserId}
            onChange={(e) => setSelectedUserId(e.target.value)}
            placeholder="Select technician..."
          >
            <option value="">Select technician...</option>
            {availableUsers.map((user) => (
              <option key={user.id} value={user.id}>
                {user.full_name}
              </option>
            ))}
          </Select>
          <Button onClick={handleAssign} disabled={!selectedUserId || isProcessing} className="w-full">
            <User className="h-4 w-4 mr-2" />
            Assign to Technician
          </Button>
        </div>
      )}

      {(incident.status === "assigned" || incident.status === "in_progress") && canResolve && (
        <div className="space-y-2">
          <Select
            value={resolutionType}
            onChange={(e) => setResolutionType(e.target.value as any)}
          >
            <option value="fixed">Fixed</option>
            <option value="duplicate">Duplicate</option>
            <option value="invalid">Invalid</option>
            <option value="deferred">Deferred</option>
          </Select>
          <textarea
            value={resolutionNotes}
            onChange={(e) => setResolutionNotes(e.target.value)}
            placeholder="Resolution notes..."
            rows={3}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
          <Button onClick={handleResolve} disabled={!resolutionNotes.trim() || isProcessing} className="w-full">
            <Wrench className="h-4 w-4 mr-2" />
            Resolve Incident
          </Button>
        </div>
      )}
    </div>
  )
}
