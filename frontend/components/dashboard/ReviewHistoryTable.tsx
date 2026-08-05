"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { FileText, ClipboardList } from "lucide-react";
import { ReviewListItem, RiskLevel } from "@/lib/types";
import RiskBadge from "@/components/review/RiskBadge";

interface ReviewHistoryTableProps {
  reviews: ReviewListItem[];
  isLoading: boolean;
}

type SortField = "timestamp" | "overall_risk_score" | "finding_count" | "filename";
type SortDirection = "asc" | "desc";

export default function ReviewHistoryTable({
  reviews,
  isLoading,
}: ReviewHistoryTableProps) {
  const router = useRouter();
  const [sortField, setSortField] = useState<SortField>("timestamp");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("desc");
    }
  };

  const sortedReviews = [...reviews].sort((a, b) => {
    const dir = sortDirection === "asc" ? 1 : -1;
    switch (sortField) {
      case "timestamp":
        return (
          dir *
          (new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
        );
      case "overall_risk_score":
        return dir * ((a.overall_risk_score || 0) - (b.overall_risk_score || 0));
      case "finding_count":
        return dir * (a.finding_count - b.finding_count);
      case "filename":
        return dir * a.filename.localeCompare(b.filename);
      default:
        return 0;
    }
  });

  const SortIcon = ({ field }: { field: SortField }) => (
    <svg
      className={`w-3.5 h-3.5 ml-1 inline-block transition-colors ${
        sortField === field ? "text-brand-400" : "text-gray-600"
      }`}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={2}
      stroke="currentColor"
    >
      {sortField === field && sortDirection === "asc" ? (
        <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 15.75l7.5-7.5 7.5 7.5" />
      ) : (
        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
      )}
    </svg>
  );

  if (isLoading) {
    return (
      <div className="glass-card overflow-hidden">
        <div className="p-6 space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex items-center gap-4">
              <div className="skeleton w-full h-12 rounded-lg" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (reviews.length === 0) {
    return (
      <div className="glass-card p-12 text-center">
        <ClipboardList className="w-12 h-12 mx-auto mb-4 text-gray-600" strokeWidth={1.5} />
        <h3 className="text-lg font-semibold text-gray-300 mb-2">
          No reviews yet
        </h3>
        <p className="text-gray-500 mb-6">
          Upload a SOW document to start your first review.
        </p>
        <a href="/" className="btn-primary">
          Upload Document
        </a>
      </div>
    );
  }

  return (
    <div className="glass-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full" id="review-history-table">
          <thead>
            <tr className="border-b border-gray-200/10">
              <th
                onClick={() => handleSort("filename")}
                className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider cursor-pointer hover:text-gray-300 transition-colors"
              >
                Filename <SortIcon field="filename" />
              </th>
              <th
                onClick={() => handleSort("timestamp")}
                className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider cursor-pointer hover:text-gray-300 transition-colors"
              >
                Date <SortIcon field="timestamp" />
              </th>
              <th
                onClick={() => handleSort("overall_risk_score")}
                className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider cursor-pointer hover:text-gray-300 transition-colors"
              >
                Risk Score <SortIcon field="overall_risk_score" />
              </th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Risk Level
              </th>
              <th
                onClick={() => handleSort("finding_count")}
                className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider cursor-pointer hover:text-gray-300 transition-colors"
              >
                Findings <SortIcon field="finding_count" />
              </th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Status
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200/5">
            {sortedReviews.map((review) => (
              <tr
                key={review.review_id}
                onClick={() => router.push(`/review/${review.review_id}`)}
                className="hover:bg-white/[0.02] cursor-pointer transition-colors group"
                id={`review-row-${review.review_id.slice(0, 8)}`}
              >
                <td className="px-6 py-4">
                  <span className="text-sm font-medium text-gray-300 group-hover:text-brand-400 transition-colors inline-flex items-center gap-1.5">
                    <FileText className="w-4 h-4 text-gray-500" strokeWidth={1.75} />
                    {review.filename}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <span className="text-sm text-gray-500">
                    {new Date(review.timestamp).toLocaleDateString("en-US", {
                      month: "short",
                      day: "numeric",
                      year: "numeric",
                    })}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <span className="text-sm font-mono font-medium text-gray-400">
                    {review.overall_risk_score?.toFixed(1) ?? "—"}
                  </span>
                </td>
                <td className="px-6 py-4">
                  {review.overall_risk_level ? (
                    <RiskBadge level={review.overall_risk_level} size="sm" />
                  ) : (
                    <span className="text-xs text-gray-600">—</span>
                  )}
                </td>
                <td className="px-6 py-4">
                  <span className="text-sm text-gray-400">
                    {review.finding_count}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <span
                    className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium ${
                      review.status === "complete"
                        ? "bg-green-500/10 text-green-400"
                        : review.status === "error"
                        ? "bg-red-500/10 text-red-400"
                        : review.status === "in_progress"
                        ? "bg-blue-500/10 text-blue-400"
                        : "bg-gray-500/10 text-gray-400"
                    }`}
                  >
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        review.status === "complete"
                          ? "bg-green-400"
                          : review.status === "error"
                          ? "bg-red-400"
                          : review.status === "in_progress"
                          ? "bg-blue-400 animate-pulse"
                          : "bg-gray-400"
                      }`}
                    />
                    {review.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
