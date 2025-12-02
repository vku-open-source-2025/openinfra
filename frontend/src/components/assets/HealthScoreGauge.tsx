import { getHealthScoreColor } from "../../utils/healthScore";

interface HealthScoreGaugeProps {
  score: number; // 0-100
  size?: number;
}

export const HealthScoreGauge: React.FC<HealthScoreGaugeProps> = ({ score, size = 200 }) => {
  const color = getHealthScoreColor(score);
  const radius = size / 2 - 10;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  const getColorClass = () => {
    switch (color) {
      case "green":
        return "stroke-green-500";
      case "yellow":
        return "stroke-yellow-500";
      case "orange":
        return "stroke-orange-500";
      default:
        return "stroke-red-500";
    }
  };

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="rgb(226 232 240)"
          strokeWidth="12"
          fill="none"
        />
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth="12"
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className={getColorClass()}
          style={{
            transition: "stroke-dashoffset 0.5s ease-in-out",
          }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-center">
          <div className={`text-4xl font-bold ${
            color === "green" ? "text-green-600" :
            color === "yellow" ? "text-yellow-600" :
            color === "orange" ? "text-orange-600" :
            "text-red-600"
          }`}>
            {score}
          </div>
          <div className="text-xs text-slate-500 mt-1">/ 100</div>
        </div>
      </div>
    </div>
  );
};
