import { AgentCardProps, DOMAIN_ICONS, DOMAIN_LABELS, RiskLevel } from "@/lib/types";
import RiskBadge from "./RiskBadge";
import ConfidenceBar from "./ConfidenceBar";
import FindingsList from "./FindingsList";

export default function AgentCard({
  agent,
  domain,
  findings,
  confidence,
  riskLevel,
}: AgentCardProps) {
  const icon = DOMAIN_ICONS[domain] || "🔍";
  const label = DOMAIN_LABELS[domain] || domain;

  // Compute dominant risk level from findings
  const getDominantRisk = (): RiskLevel => {
    if (!findings || findings.length === 0) return "LOW";
    const highCount = findings.filter((f) => f.risk_level === "HIGH").length;
    const medCount = findings.filter((f) => f.risk_level === "MEDIUM").length;
    if (highCount > 0) return "HIGH";
    if (medCount > 0) return "MEDIUM";
    return "LOW";
  };

  const dominantRisk = riskLevel || getDominantRisk();

  const borderColor = {
    HIGH: "border-red-500/20 hover:border-red-500/40",
    MEDIUM: "border-amber-500/20 hover:border-amber-500/40",
    LOW: "border-green-500/20 hover:border-green-500/40",
  };

  const glowColor = {
    HIGH: "hover:shadow-red-500/5",
    MEDIUM: "hover:shadow-amber-500/5",
    LOW: "hover:shadow-green-500/5",
  };

  return (
    <div
      className={`glass-card border ${borderColor[dominantRisk]} ${glowColor[dominantRisk]} hover:shadow-xl transition-all duration-300 animate-slide-up`}
      id={`agent-card-${domain}`}
    >
      {/* Card Header */}
      <div className="p-5 pb-4 border-b border-gray-200/5">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{icon}</span>
            <div>
              <h3 className="font-semibold text-gray-200">{label}</h3>
              <p className="text-xs text-gray-500">
                {findings.length} finding{findings.length !== 1 ? "s" : ""}
              </p>
            </div>
          </div>
          <RiskBadge level={dominantRisk} />
        </div>

        {/* Confidence Bar */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs text-gray-500">Agent Confidence</span>
          </div>
          <ConfidenceBar confidence={confidence} size="sm" />
        </div>
      </div>

      {/* Findings List */}
      <div className="p-5 pt-4 max-h-[400px] overflow-y-auto">
        <FindingsList findings={findings} />
      </div>
    </div>
  );
}
