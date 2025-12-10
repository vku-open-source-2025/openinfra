import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { IncidentCard } from "./IncidentCard";
import { incidentsApi } from "../../api/incidents";
import type { Incident } from "../../types/incident";
import { ChevronDown, ChevronRight, Copy, Link as LinkIcon } from "lucide-react";
import { useNavigate } from "@tanstack/react-router";

interface DuplicateGroupCardProps {
  primaryIncident: Incident;
  duplicateIncidents: Incident[];
  index?: number; // Index for alternating colors
  onClick?: () => void;
}

export const DuplicateGroupCard: React.FC<DuplicateGroupCardProps> = ({
  primaryIncident,
  duplicateIncidents,
  index = 0,
  onClick,
}) => {
  const navigate = useNavigate();
  // Default to collapsed - hide duplicate tickets by default
  const [isExpanded, setIsExpanded] = useState(false);
  
  // Alternating colors: even = blue, odd = purple
  const isEven = index % 2 === 0;
  const primaryBgColor = isEven ? "bg-blue-50" : "bg-purple-50";
  const primaryHoverColor = isEven ? "hover:bg-blue-100" : "hover:bg-purple-100";
  const primaryTextColor = isEven ? "text-blue-600" : "text-purple-600";
  const primaryBadgeBg = isEven ? "bg-blue-200" : "bg-purple-200";
  const primaryBadgeText = isEven ? "text-blue-700" : "text-purple-700";
  const borderColor = isEven ? "border-blue-200" : "border-purple-200";

  return (
    <div className={`bg-white rounded-lg border-2 ${borderColor} overflow-hidden shadow-sm`}>
      {/* Primary Ticket Header */}
      <div
        className={`p-4 border-b ${borderColor} ${primaryBgColor} ${primaryHoverColor} transition-colors cursor-pointer`}
        onClick={() => {
          if (onClick) onClick();
          else navigate({ to: `/admin/incidents/${primaryIncident.id}` });
        }}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setIsExpanded(!isExpanded);
                }}
                className={`p-1 ${isEven ? "hover:bg-blue-200" : "hover:bg-purple-200"} rounded transition-colors`}
              >
                {isExpanded ? (
                  <ChevronDown className={`h-4 w-4 ${primaryTextColor}`} />
                ) : (
                  <ChevronRight className={`h-4 w-4 ${primaryTextColor}`} />
                )}
              </button>
              <span className={`text-xs font-semibold ${primaryBadgeText} ${primaryBadgeBg} px-2 py-1 rounded`}>
                Ticket chính
              </span>
              <span className="text-xs text-slate-500">
                ({duplicateIncidents.length} ticket trùng lặp)
              </span>
            </div>
            <h3 className="font-semibold text-slate-900">{primaryIncident.title}</h3>
            <p className="text-sm text-slate-600 mt-1 line-clamp-1">
              {primaryIncident.description}
            </p>
          </div>
          <div className="flex flex-col items-end gap-1 ml-4">
            <span className="text-xs text-slate-500">
              {primaryIncident.incident_number || `#${primaryIncident.id.slice(-8)}`}
            </span>
          </div>
        </div>
      </div>

      {/* Duplicate Tickets */}
      {isExpanded && (
        <div className={`ml-6 divide-y ${isEven ? "divide-blue-100" : "divide-purple-100"}`}>
          {duplicateIncidents.map((duplicate, index) => {
            // Alternate duplicate ticket colors within group
            const isDuplicateEven = index % 2 === 0;
            const duplicateBg = isDuplicateEven 
              ? (isEven ? "bg-blue-50/30" : "bg-purple-50/30")
              : (isEven ? "bg-slate-50" : "bg-slate-100");
            const duplicateHover = isEven ? "hover:bg-blue-100" : "hover:bg-purple-100";
            const duplicateBorder = isEven ? "border-orange-400" : "border-orange-500";
            
            return (
            <div
              key={duplicate.id}
              className={`p-4 ${duplicateBg} ${duplicateHover} transition-colors cursor-pointer border-l-4 ${duplicateBorder}`}
              onClick={() => {
                navigate({ to: `/admin/incidents/${duplicate.id}` });
              }}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <Copy className="h-3.5 w-3.5 text-orange-600" />
                    <span className="text-xs font-semibold text-orange-700 bg-orange-100 px-2 py-0.5 rounded">
                      Trùng lặp #{index + 1}
                    </span>
                    {duplicate.resolution_notes && (
                      <span className="text-xs text-slate-500 italic">
                        {duplicate.resolution_notes}
                      </span>
                    )}
                  </div>
                  <h4 className="font-medium text-slate-900 text-sm">{duplicate.title}</h4>
                  <p className="text-xs text-slate-600 mt-1 line-clamp-2">
                    {duplicate.description}
                  </p>
                  <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
                    <span>
                      {new Date(duplicate.created_at).toLocaleDateString("vi-VN")}
                    </span>
                    {duplicate.resolved_at && (
                      <span className="text-orange-600">
                        Đã giải quyết: {new Date(duplicate.resolved_at).toLocaleDateString("vi-VN")}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex flex-col items-end gap-1 ml-4">
                  <span className="text-xs text-slate-500">
                    {duplicate.incident_number || `#${duplicate.id.slice(-8)}`}
                  </span>
                </div>
              </div>
            </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
