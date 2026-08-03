interface ConfidenceBarProps {
  confidence: number; // 0.0 to 1.0
  showLabel?: boolean;
  size?: "sm" | "md";
}

export default function ConfidenceBar({
  confidence,
  showLabel = true,
  size = "md",
}: ConfidenceBarProps) {
  const percentage = Math.round(confidence * 100);

  // Color based on confidence level
  const getColor = () => {
    if (confidence >= 0.8) return "from-green-400 to-emerald-500";
    if (confidence >= 0.6) return "from-blue-400 to-cyan-500";
    if (confidence >= 0.4) return "from-amber-400 to-orange-500";
    return "from-red-400 to-rose-500";
  };

  const heightClass = size === "sm" ? "h-1.5" : "h-2.5";

  return (
    <div className="flex items-center gap-3">
      <div className={`flex-1 ${heightClass} rounded-full bg-gray-200 dark:bg-surface-700 overflow-hidden`}>
        <div
          className={`h-full rounded-full bg-gradient-to-r ${getColor()} transition-all duration-700 ease-out`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-xs font-mono font-medium text-gray-400 min-w-[3rem] text-right">
          {percentage}%
        </span>
      )}
    </div>
  );
}
