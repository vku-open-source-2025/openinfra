import { IncidentStatusBadge } from "./IncidentStatusBadge"
import type { Incident } from "../../types/incident"
import { MapPin, Clock, User } from "lucide-react"
import { format } from "date-fns"

interface IncidentCardProps {
  incident: Incident
  onClick?: () => void
}

export const IncidentCard: React.FC<IncidentCardProps> = ({ incident, onClick }) => {
  return (
    <div
      onClick={onClick}
      className="bg-white rounded-lg border border-slate-200 p-4 hover:shadow-md transition-shadow cursor-pointer"
    >
      <div className="flex items-start justify-between mb-2">
        <h3 className="font-semibold text-slate-900">{incident.title}</h3>
        <IncidentStatusBadge status={incident.status} severity={incident.severity} />
      </div>
      <p className="text-sm text-slate-600 mb-3 line-clamp-2">{incident.description}</p>
      <div className="flex items-center gap-4 text-xs text-slate-500">
        <div className="flex items-center gap-1">
          <MapPin className="h-3 w-3" />
          <span>{incident.location?.address || "Location not specified"}</span>
        </div>
        <div className="flex items-center gap-1">
          <Clock className="h-3 w-3" />
          <span>{format(new Date(incident.created_at), "MMM d, yyyy")}</span>
        </div>
        {incident.assigned_to && (
          <div className="flex items-center gap-1">
            <User className="h-3 w-3" />
            <span>Assigned</span>
          </div>
        )}
      </div>
      {incident.upvotes > 0 && (
        <div className="mt-2 text-xs text-slate-500">
          {incident.upvotes} upvote{incident.upvotes !== 1 ? "s" : ""}
        </div>
      )}
    </div>
  )
}
