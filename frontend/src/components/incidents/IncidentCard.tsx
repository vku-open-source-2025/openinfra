import { IncidentStatusBadge } from "./IncidentStatusBadge"
import type { Incident } from "../../types/incident"
import { MapPin, Clock, User, Box } from "lucide-react"
import { format } from "date-fns"

interface IncidentCardProps {
  incident: Incident
  onClick?: () => void
}

export const IncidentCard: React.FC<IncidentCardProps> = ({ incident, onClick }) => {
  const assetDisplayName = incident.asset
    ? incident.asset.name || incident.asset.asset_code || incident.asset.feature_type
    : null;

  return (
    <div
      onClick={onClick}
      className="bg-white rounded-lg border border-slate-200 p-4 hover:shadow-md transition-shadow cursor-pointer"
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-slate-900">{incident.title}</h3>
          {assetDisplayName && (
            <div className="flex items-center gap-1.5 mt-1">
              <Box className="h-3.5 w-3.5 text-blue-500 flex-shrink-0" />
              <span className="text-sm text-blue-600 font-medium truncate">
                {assetDisplayName}
              </span>
              {incident.asset?.category && (
                <span className="text-xs text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">
                  {incident.asset.category}
                </span>
              )}
            </div>
          )}
        </div>
        <IncidentStatusBadge status={incident.status} severity={incident.severity} />
      </div>
      <p className="text-sm text-slate-600 mb-3 line-clamp-2">{incident.description}</p>
      <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
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
        {incident.cost_status === 'pending' && (
          <div className="flex items-center gap-1 text-orange-600 font-medium">
            <span>$ Approval Needed</span>
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
