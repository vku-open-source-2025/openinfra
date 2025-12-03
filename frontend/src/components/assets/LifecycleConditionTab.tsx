import { useQuery } from "@tanstack/react-query";
import { assetsApi } from "../../api/assets";
import { Skeleton } from "../ui/skeleton";
import { HealthScoreGauge } from "./HealthScoreGauge";
import { getHealthScoreColor, getHealthScoreLabel } from "../../utils/healthScore";
import { calculateRemainingLifespan } from "../../utils/healthScore";
import { format } from "date-fns";
import type { Asset } from "../../types/asset";
import { AlertTriangle, TrendingUp, TrendingDown, Minus } from "lucide-react";

interface LifecycleConditionTabProps {
  assetId: string;
  asset: Asset;
}

const LifecycleConditionTab: React.FC<LifecycleConditionTabProps> = ({ assetId, asset }) => {
  const { data: healthData, isLoading } = useQuery({
    queryKey: ["asset", "health-score", assetId],
    queryFn: () => assetsApi.getHealthScore(assetId),
  });

  const healthScore = asset.lifecycle?.health_score ?? healthData?.health_score ?? 0;
  const healthStatus = healthData?.health_status;
  const healthColor = getHealthScoreColor(healthScore);
  const healthLabel = healthStatus || getHealthScoreLabel(healthScore);

  const currentAge = asset.lifecycle?.commissioned_date
    ? Math.floor((new Date().getTime() - new Date(asset.lifecycle.commissioned_date).getTime()) / (1000 * 60 * 60 * 24 * 365))
    : 0;
  const designedLifespan = asset.lifecycle?.designed_lifespan_years ?? 0;
  const remainingLifespanPercent = calculateRemainingLifespan(currentAge, designedLifespan);

  if (isLoading) {
    return <Skeleton className="h-96 w-full" />;
  }

  return (
    <div className="space-y-6">
      {/* Health Score Gauge */}
      <div className="bg-slate-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Health Score</h3>
        <div className="flex items-center justify-center">
          <HealthScoreGauge score={healthScore} />
        </div>
        <div className="text-center mt-4">
          <p className={`text-2xl font-bold ${
            healthColor === "green" ? "text-green-600" :
            healthColor === "yellow" ? "text-yellow-600" :
            healthColor === "orange" ? "text-orange-600" :
            "text-red-600"
          }`}>
            {healthScore.toFixed(1)}/100
          </p>
          <p className="text-sm text-slate-600 mt-1 capitalize">{healthLabel}</p>
        </div>
      </div>

      {/* Remaining Lifespan */}
      {designedLifespan > 0 && (
        <div className="bg-slate-50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Remaining Lifespan</h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm text-slate-600 mb-2">
                <span>Current Age: {currentAge} years</span>
                <span>Designed Lifespan: {designedLifespan} years</span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-8 relative overflow-hidden">
                <div
                  className={`h-full transition-all ${
                    remainingLifespanPercent >= 50 ? "bg-green-500" :
                    remainingLifespanPercent >= 25 ? "bg-yellow-500" :
                    "bg-red-500"
                  }`}
                  style={{ width: `${remainingLifespanPercent}%` }}
                />
                <div className="absolute inset-0 flex items-center justify-center text-xs font-semibold text-slate-900">
                  {remainingLifespanPercent}% Remaining ({asset.lifecycle?.remaining_lifespan_years || 0} years)
                </div>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <label className="text-xs text-slate-500 uppercase tracking-wide">Current Age</label>
                <p className="text-lg font-semibold text-slate-900 mt-1">{currentAge} years</p>
              </div>
              <div>
                <label className="text-xs text-slate-500 uppercase tracking-wide">Remaining Life</label>
                <p className="text-lg font-semibold text-slate-900 mt-1">
                  {asset.lifecycle?.remaining_lifespan_years || 0} years
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Current Age vs Designed Lifespan Chart */}
      {designedLifespan > 0 && (
        <div className="bg-slate-50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Age Comparison</h3>
          <div className="space-y-2">
            <div>
              <div className="flex justify-between text-xs text-slate-600 mb-1">
                <span>Current Age</span>
                <span>{currentAge} years</span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-4">
                <div
                  className="bg-blue-500 h-4 rounded-full"
                  style={{ width: `${Math.min(100, (currentAge / designedLifespan) * 100)}%` }}
                />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-xs text-slate-600 mb-1">
                <span>Designed Lifespan</span>
                <span>{designedLifespan} years</span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-4">
                <div className="bg-slate-400 h-4 rounded-full" style={{ width: "100%" }} />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Health Score Breakdown */}
      {healthData?.breakdown && (
        <div className="bg-slate-50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Health Score Breakdown</h3>
          <div className="space-y-3">
            <FactorItem
              label="Condition (30%)"
              value={healthData.breakdown.condition_score}
              trend="neutral"
            />
            <FactorItem
              label="Status (20%)"
              value={healthData.breakdown.status_score}
              trend="neutral"
            />
            <FactorItem
              label="Maintenance (25%)"
              value={healthData.breakdown.maintenance_score}
              trend="up"
            />
            <FactorItem
              label="Incidents (15%)"
              value={healthData.breakdown.incident_score}
              trend="neutral"
            />
            <FactorItem
              label="Age (10%)"
              value={healthData.breakdown.age_score}
              trend="down"
            />
          </div>
        </div>
      )}

      {/* Trend Graph Placeholder */}
      <div className="bg-slate-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Health Score Trend</h3>
        <div className="h-64 flex items-center justify-center text-slate-400 border-2 border-dashed border-slate-300 rounded">
          <div className="text-center">
            <TrendingUp size={48} className="mx-auto mb-2 opacity-50" />
            <p>Health score trend graph</p>
            <p className="text-xs mt-1">(Chart visualization would be implemented here)</p>
          </div>
        </div>
      </div>
    </div>
  );
};

interface FactorItemProps {
  label: string;
  value: number;
  trend: "up" | "down" | "neutral";
}

const FactorItem: React.FC<FactorItemProps> = ({ label, value, trend }) => {
  const getColor = (val: number) => {
    if (val >= 80) return "text-green-600";
    if (val >= 60) return "text-yellow-600";
    if (val >= 40) return "text-orange-600";
    return "text-red-600";
  };

  const TrendIcon = trend === "up" ? TrendingUp : trend === "down" ? TrendingDown : Minus;

  return (
    <div className="flex items-center justify-between p-3 bg-white rounded border border-slate-200">
      <div className="flex items-center gap-3">
        <TrendIcon size={16} className="text-slate-400" />
        <span className="text-sm font-medium text-slate-900">{label}</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="w-24 bg-slate-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full ${getColor(value).replace("text-", "bg-")}`}
            style={{ width: `${value}%` }}
          />
        </div>
        <span className={`text-sm font-semibold w-12 text-right ${getColor(value)}`}>
          {value}/100
        </span>
      </div>
    </div>
  );
};

export default LifecycleConditionTab;
