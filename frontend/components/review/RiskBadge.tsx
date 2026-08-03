import { RiskLevel } from "@/lib/types";

interface RiskBadgeProps {
  level: RiskLevel;
  size?: "sm" | "md" | "lg";
}

export default function RiskBadge({ level, size = "md" }: RiskBadgeProps) {
  const sizeClasses = {
    sm: "px-2 py-0.5 text-[10px]",
    md: "px-3 py-1 text-xs",
    lg: "px-4 py-1.5 text-sm",
  };

  const levelClasses = {
    HIGH: "risk-badge-high",
    MEDIUM: "risk-badge-medium",
    LOW: "risk-badge-low",
  };

  const icons = {
    HIGH: "🔴",
    MEDIUM: "🟡",
    LOW: "🟢",
  };

  return (
    <span
      className={`${levelClasses[level]} ${sizeClasses[size]}`}
      id={`risk-badge-${level.toLowerCase()}`}
    >
      <span className="text-[0.6em]">{icons[level]}</span>
      {level}
    </span>
  );
}
