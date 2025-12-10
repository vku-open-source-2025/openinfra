import { IncidentStatusBadge } from "./IncidentStatusBadge"
import type { Incident, IncidentLocation } from "../../types/incident"
import { MapPin, Clock, User, Box, CheckCircle, AlertTriangle, Clock as ClockIcon, XCircle } from "lucide-react"
import { format } from "date-fns"

// Helper function to get display string for incident location
const getLocationDisplay = (location?: IncidentLocation): string => {
  if (!location) return "Vị trí chưa được xác định";
  
  // First, try geometry.coordinates [lng, lat] - more reliable than address
  if (location.geometry?.coordinates && Array.isArray(location.geometry.coordinates)) {
    const coords = location.geometry.coordinates;
    if (coords.length >= 2 && typeof coords[0] === 'number' && typeof coords[1] === 'number') {
      return `${(coords[1] as number).toFixed(6)}, ${(coords[0] as number).toFixed(6)}`;
    }
  }
  
  // Then, try coordinates.latitude/longitude
  if (location.coordinates?.latitude && location.coordinates?.longitude) {
    return `${location.coordinates.latitude.toFixed(6)}, ${location.coordinates.longitude.toFixed(6)}`;
  }
  
  // Finally, try address (but skip if it's literally "Location not specified")
  if (location.address && !["Location not specified", "Vị trí chưa được xác định"].includes(location.address)) {
    return location.address;
  }
  
  return "Vị trí chưa được xác định";
};

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
            <span>Đã xác minh {scorePercent && `(${scorePercent}%)`}</span>
          </div>
        );
            case 'to_be_verified':
        // Differentiate spam risk vs likely safe
          if (isSpamRisk) {
          return (
              <div className="flex items-center gap-1 text-red-600 bg-red-50 px-2 py-1 rounded-full text-xs font-medium" title={incident.ai_verification_reason || `Mức tin cậy thấp: ${scorePercent}% xác suất hợp lệ`}>
              <AlertTriangle className="h-3.5 w-3.5" />
              <span>Nguy cơ spam {scorePercent !== null && `(${scorePercent}%)`}</span>
            </div>
          );
        }
        return (
            <div className="flex items-center gap-1 text-amber-600 bg-amber-50 px-2 py-1 rounded-full text-xs font-medium" title={incident.ai_verification_reason || `Mức độ tin cậy: ${scorePercent}% xác suất hợp lệ`}>
            <AlertTriangle className="h-3.5 w-3.5" />
            <span>Chờ xác minh {scorePercent !== null && `(${scorePercent}%)`}</span>
          </div>
        );
      case 'failed':
        return (
          <div className="flex items-center gap-1 text-red-600 bg-red-50 px-2 py-1 rounded-full text-xs font-medium" title={incident.ai_verification_reason}>
            <XCircle className="h-3.5 w-3.5" />
            <span>Xác minh thất bại</span>
          </div>
        );
      default:
        return (
          <div className="flex items-center gap-1 text-slate-500 bg-slate-100 px-2 py-1 rounded-full text-xs font-medium">
            <ClockIcon className="h-3.5 w-3.5" />
            <span>Đang chờ</span>
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
              <Box className="h-3.5 w-3.5 text-blue-500 shrink-0" />
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
          <span>{getLocationDisplay(incident.location)}</span>
        </div>
        <div className="flex items-center gap-1">
          <Clock className="h-3 w-3" />
          <span>{new Date(incident.created_at).toLocaleDateString('vi-VN')}</span>
        </div>
        {incident.assigned_to && (
          <div className="flex items-center gap-1">
            <User className="h-3 w-3" />
            <span>Đã phân công</span>
          </div>
        )}
        {incident.cost_status === 'pending' && (
            <div className="flex items-center gap-1 text-orange-600 font-medium">
            <span>Chờ phê duyệt chi phí</span>
          </div>
        )}
      </div>
          {incident.upvotes > 0 && (
        <div className="mt-2 text-xs text-slate-500">
          {incident.upvotes} lượt thích
        </div>
      )}
    </div>
  )
}
