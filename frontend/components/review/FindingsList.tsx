"use client";

import { useState } from "react";
import { Finding } from "@/lib/types";
import RiskBadge from "./RiskBadge";

interface FindingsListProps {
  findings: Finding[];
}

export default function FindingsList({ findings }: FindingsListProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  if (!findings || findings.length === 0) {
    return (
      <p className="text-sm text-gray-500 italic py-3">
        No findings in this domain.
      </p>
    );
  }

  return (
    <div className="space-y-2">
      {findings.map((finding, index) => (
        <div
          key={index}
          className="group rounded-xl border border-gray-200/10 hover:border-gray-200/20 bg-white/[0.02] hover:bg-white/[0.04] transition-all duration-200"
        >
          {/* Finding Header (clickable) */}
          <button
            onClick={() =>
              setExpandedIndex(expandedIndex === index ? null : index)
            }
            className="w-full flex items-start gap-3 p-4 text-left"
            id={`finding-${index}`}
          >
            {/* Expand indicator */}
            <svg
              className={`w-4 h-4 mt-0.5 text-gray-500 transition-transform duration-200 flex-shrink-0 ${
                expandedIndex === index ? "rotate-90" : ""
              }`}
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M8.25 4.5l7.5 7.5-7.5 7.5"
              />
            </svg>

            {/* Finding text */}
            <div className="flex-1 min-w-0">
              <p className="text-sm text-gray-300 leading-relaxed line-clamp-2 group-hover:text-gray-200">
                {finding.finding}
              </p>
            </div>

            {/* Risk badge */}
            <RiskBadge level={finding.risk_level} size="sm" />
          </button>

          {/* Expanded Details */}
          {expandedIndex === index && (
            <div className="px-4 pb-4 pt-0 ml-7 border-t border-gray-200/5 animate-fade-in">
              {/* Page reference */}
              {finding.page_reference && (
                <div className="flex items-center gap-2 mt-3 mb-2">
                  <svg className="w-3.5 h-3.5 text-gray-500" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                  </svg>
                  <span className="text-xs text-gray-500">
                    {finding.page_reference}
                  </span>
                </div>
              )}

              {/* Confidence */}
              <div className="flex items-center gap-2 mb-3">
                <span className="text-xs text-gray-500">Confidence:</span>
                <span className="text-xs font-mono font-medium text-gray-400">
                  {Math.round(finding.confidence * 100)}%
                </span>
              </div>

              {/* Recommendation */}
              <div className="p-3 rounded-lg bg-brand-500/5 border border-brand-500/10">
                <p className="text-xs font-medium text-brand-400 mb-1">
                  💡 Recommendation
                </p>
                <p className="text-sm text-gray-400 leading-relaxed">
                  {finding.recommendation}
                </p>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
