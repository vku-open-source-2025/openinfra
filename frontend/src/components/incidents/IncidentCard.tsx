import { IncidentStatusBadge } from "./IncidentStatusBadge"
import type { Incident } from "../../types/incident"
import { MapPin, Clock, User, Box, CheckCircle, AlertTriangle, Clock as ClockIcon, XCircle } from "lucide-react"
import { format } from "date-fns"

interface IncidentCardProps {
  incident: Incident
  onClick?: () => void
}

export const IncidentCard: React.FC<IncidentCardProps> = ({ incident, onClick }) => {
  const assetDisplayName = incident.asset
    ? incident.asset.name || incident.asset.asset_code || incident.asset.feature_type
    : null;

  const getVerificationBadge = () => {
    const status = incident.ai_verification_status || 'pending';
    const score = incident.ai_confidence_score;
    const scorePercent = score !== null && score !== undefined ? Math.round(score * 100) : null;
    const isSpamRisk = score !== null && score !== undefined && score < 0.5;

    switch (status) {
      case 'verified':
        return (
          <div className="flex items-center gap-1 text-green-600 bg-green-50 px-2 py-1 rounded-full text-xs font-medium" title={incident.ai_verification_reason}>
            <CheckCircle className="h-3.5 w-3.5" />
            <span>Safe {scorePercent && `(${scorePercent}%)`}</span>
          </div>
        );
      case 'to_be_verified':
        // Differentiate spam risk vs likely safe
        if (isSpamRisk) {
          return (
            <div className="flex items-center gap-1 text-red-600 bg-red-50 px-2 py-1 rounded-full text-xs font-medium" title={incident.ai_verification_reason}>
              <AlertTriangle className="h-3.5 w-3.5" />
              <span>Spam Risk {scorePercent !== null && `(${scorePercent}%)`}</span>
            </div>
          );
        }
        return (
          <div className="flex items-center gap-1 text-amber-600 bg-amber-50 px-2 py-1 rounded-full text-xs font-medium" title={incident.ai_verification_reason}>
            <AlertTriangle className="h-3.5 w-3.5" />
            <span>To Verify {scorePercent !== null && `(${scorePercent}%)`}</span>
          </div>
        );
      case 'failed':
        return (
          <div className="flex items-center gap-1 text-red-600 bg-red-50 px-2 py-1 rounded-full text-xs font-medium" title={incident.ai_verification_reason}>
            <XCircle className="h-3.5 w-3.5" />
            <span>Check Failed</span>
          </div>
        );
      default:
        return (
          <div className="flex items-center gap-1 text-slate-500 bg-slate-100 px-2 py-1 rounded-full text-xs font-medium">
            <ClockIcon className="h-3.5 w-3.5" />
            <span>Pending</span>
          </div>
        );
    }
  };

  return (
    <div
      onClick={onClick}
      className="bg-white rounded-lg border border-slate-200 p-4 hover:shadow-md transition-shadow cursor-pointer"
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-slate-900">{incident.title}</h3>
          {assetDisplayName && incident.asset?.id && (
            <div className="flex items-center gap-1.5 mt-1">
              <Box className="h-3.5 w-3.5 text-blue-500 flex-shrink-0" />
              <a
                href={`/admin/assets/${incident.asset.id}`}
                onClick={(e) => e.stopPropagation()}
                className="text-sm text-blue-600 font-medium truncate hover:underline hover:text-blue-800"
              >
                {assetDisplayName}
              </a>
              {incident.asset?.category && (
                <span className="text-xs text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">
                  {incident.asset.category}
                </span>
              )}
            </div>
          )}
        </div>
        <div className="flex flex-col items-end gap-1">
          <IncidentStatusBadge status={incident.status} severity={incident.severity} />
          {getVerificationBadge()}
        </div>
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
