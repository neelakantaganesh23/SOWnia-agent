"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useReviewStore } from "@/store/reviewStore";
import { getResults, downloadPdfReport, downloadAnnotatedPdf } from "@/lib/api";
import {
  FullReviewResult,
  DOMAIN_LABELS,
  DOMAIN_ICONS,
  RiskLevel,
  RISK_COLORS,
} from "@/lib/types";
import AgentCard from "@/components/review/AgentCard";
import RiskBadge from "@/components/review/RiskBadge";

export default function ReviewResultsPage() {
  const params = useParams();
  const reviewId = params.id as string;

  const [review, setReview] = useState<FullReviewResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);
  const [isDownloadingAnnotated, setIsDownloadingAnnotated] = useState(false);

  // Poll for results
  useEffect(() => {
    if (!reviewId) return;

    let isCancelled = false;
    let timeoutId: NodeJS.Timeout;

    const poll = async () => {
      try {
        const result = await getResults(reviewId);
        if (isCancelled) return;

        setReview(result);

        if (result.status === "complete" || result.status === "error") {
          setIsLoading(false);
          return;
        }

        // Continue polling every 3 seconds
        timeoutId = setTimeout(poll, 3000);
      } catch (err: any) {
        if (isCancelled) return;
        setError(err.response?.data?.detail || err.message);
        setIsLoading(false);
      }
    };

    poll();

    return () => {
      isCancelled = true;
      clearTimeout(timeoutId);
    };
  }, [reviewId]);

  const handleDownloadPdf = async () => {
    setIsDownloading(true);
    try {
      const blob = await downloadPdfReport(reviewId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `sownia_report_${reviewId.slice(0, 8)}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setError("Failed to download PDF report.");
    } finally {
      setIsDownloading(false);
    }
  };

  const handleDownloadJson = () => {
    if (!review) return;
    const blob = new Blob([JSON.stringify(review, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `sownia_review_${reviewId.slice(0, 8)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleDownloadAnnotatedPdf = async () => {
    setIsDownloadingAnnotated(true);
    try {
      const blob = await downloadAnnotatedPdf(reviewId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${review?.filename?.replace(/\.pdf$/i, "") || "document"}_annotated.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to download annotated PDF. This feature is only available for PDF uploads.");
    } finally {
      setIsDownloadingAnnotated(false);
    }
  };

  // Loading skeleton
  if (isLoading && (!review || review.status !== "complete")) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-12 page-enter">
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-3 mb-6">
            <div className="w-8 h-8 border-3 border-brand-400 border-t-transparent rounded-full animate-spin" />
            <span className="text-lg font-medium text-gray-300">
              AI agents are reviewing your document...
            </span>
          </div>

          {/* Agent status indicators */}
          <div className="flex flex-wrap justify-center gap-4 mt-6">
            {Object.entries(DOMAIN_LABELS).map(([domain, label]) => {
              const hasFindings =
                review?.agents?.[domain]?.findings?.length ?? 0;
              const isComplete = hasFindings > 0;

              return (
                <div
                  key={domain}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl border ${
                    isComplete
                      ? "border-green-500/30 bg-green-500/5"
                      : "border-gray-700 bg-surface-800/50"
                  }`}
                >
                  <span className="text-lg">{DOMAIN_ICONS[domain]}</span>
                  <span className="text-sm text-gray-400">{label}</span>
                  {isComplete ? (
                    <svg
                      className="w-4 h-4 text-green-400"
                      fill="none"
                      viewBox="0 0 24 24"
                      strokeWidth={2}
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M4.5 12.75l6 6 9-13.5"
                      />
                    </svg>
                  ) : (
                    <div className="w-4 h-4 border-2 border-gray-500 border-t-transparent rounded-full animate-spin" />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Skeleton Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="glass-card p-6 space-y-4">
              <div className="flex items-center gap-3">
                <div className="skeleton w-10 h-10 rounded-xl" />
                <div className="skeleton w-32 h-5 rounded" />
              </div>
              <div className="skeleton w-full h-3 rounded" />
              <div className="space-y-2">
                <div className="skeleton w-full h-12 rounded-lg" />
                <div className="skeleton w-full h-12 rounded-lg" />
                <div className="skeleton w-3/4 h-12 rounded-lg" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="max-w-2xl mx-auto px-6 py-20 text-center">
        <div className="text-5xl mb-4">⚠️</div>
        <h2 className="text-2xl font-bold text-gray-200 mb-2">Review Error</h2>
        <p className="text-gray-400 mb-6">{error}</p>
        <a href="/" className="btn-primary">
          ← Upload New Document
        </a>
      </div>
    );
  }

  if (!review) return null;

  const totalFindings = Object.values(review.agents || {}).reduce(
    (sum, agent) => sum + (agent.findings?.length || 0),
    0
  );

  return (
    <div className="max-w-7xl mx-auto px-6 py-10 page-enter">
      {/* Header */}
      <div className="mb-10">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-100 mb-1">
              Review Results
            </h1>
            <p className="text-gray-500">
              📄 {review.filename} • {new Date(review.timestamp).toLocaleString()}
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleDownloadJson}
              className="btn-secondary"
              id="download-json-btn"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={2}
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"
                />
              </svg>
              JSON
            </button>
            <button
              onClick={handleDownloadPdf}
              disabled={isDownloading}
              className="btn-secondary"
              id="download-pdf-btn"
            >
              {isDownloading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <svg
                  className="w-4 h-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={2}
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m.75 12l3 3m0 0l3-3m-3 3v-6m-1.5-9H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
                  />
                </svg>
              )}
              PDF Report
            </button>
            <button
              onClick={handleDownloadAnnotatedPdf}
              disabled={isDownloadingAnnotated}
              className="btn-primary"
              id="download-annotated-pdf-btn"
              title="Download original PDF with highlighted findings"
            >
              {isDownloadingAnnotated ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <svg
                  className="w-4 h-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={2}
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M9.53 16.122a3 3 0 00-5.78 1.128 2.25 2.25 0 01-2.4 2.245 4.5 4.5 0 008.4-2.245c0-.399-.078-.78-.22-1.128zm0 0a15.998 15.998 0 003.388-1.62m-5.043-.025a15.994 15.994 0 011.622-3.395m3.42 3.42a15.995 15.995 0 004.764-4.648l3.876-5.814a1.151 1.151 0 00-1.597-1.597L14.146 6.32a15.996 15.996 0 00-4.649 4.763m3.42 3.42a6.776 6.776 0 00-3.42-3.42"
                  />
                </svg>
              )}
              Annotated PDF
            </button>
          </div>
        </div>
      </div>

      {/* Overall Risk Score */}
      <div className="glass-card p-8 mb-8">
        <div className="flex flex-col md:flex-row items-center gap-8">
          {/* Risk Gauge */}
          <div className="text-center flex-shrink-0">
            <div className="relative w-32 h-32 mx-auto">
              <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
                <circle
                  cx="60"
                  cy="60"
                  r="50"
                  fill="none"
                  stroke="currentColor"
                  className="text-surface-700"
                  strokeWidth="8"
                />
                <circle
                  cx="60"
                  cy="60"
                  r="50"
                  fill="none"
                  stroke={
                    RISK_COLORS[
                      (review.overall_risk_level as RiskLevel) || "MEDIUM"
                    ]
                  }
                  strokeWidth="8"
                  strokeLinecap="round"
                  strokeDasharray={`${
                    ((review.overall_risk_score || 0) / 10) * 314
                  } 314`}
                  className="transition-all duration-1000 ease-out"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-3xl font-bold text-gray-100">
                  {review.overall_risk_score?.toFixed(1) || "N/A"}
                </span>
                <span className="text-xs text-gray-500">/10.0</span>
              </div>
            </div>
            {review.overall_risk_level && (
              <div className="mt-3">
                <RiskBadge level={review.overall_risk_level} size="lg" />
              </div>
            )}
          </div>

          {/* Summary */}
          <div className="flex-1">
            <h2 className="text-xl font-bold text-gray-200 mb-3">
              Executive Summary
            </h2>
            <p className="text-gray-400 leading-relaxed whitespace-pre-line text-sm">
              {review.summary || "No summary available."}
            </p>
            <div className="flex items-center gap-6 mt-4 text-sm text-gray-500">
              <span>📋 {totalFindings} total findings</span>
              <span>
                🔴{" "}
                {Object.values(review.agents || {}).reduce(
                  (sum, a) =>
                    sum +
                    (a.findings?.filter((f) => f.risk_level === "HIGH").length ||
                      0),
                  0
                )}{" "}
                high risk
              </span>
              <span>🤖 5 agents</span>
            </div>
          </div>
        </div>
      </div>

      {/* Agent Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {Object.entries(review.agents || {}).map(([domain, agentResult]) => (
          <AgentCard
            key={domain}
            agent={agentResult.agent || domain}
            domain={domain}
            findings={agentResult.findings || []}
            confidence={agentResult.agent_confidence || 0}
            riskLevel={
              (agentResult.findings?.some((f) => f.risk_level === "HIGH")
                ? "HIGH"
                : agentResult.findings?.some((f) => f.risk_level === "MEDIUM")
                ? "MEDIUM"
                : "LOW") as RiskLevel
            }
          />
        ))}
      </div>
    </div>
  );
}
