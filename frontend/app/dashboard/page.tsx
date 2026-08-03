"use client";

import { useEffect, useState } from "react";
import { useReviewStore } from "@/store/reviewStore";
import { RiskLevel } from "@/lib/types";
import ReviewHistoryTable from "@/components/dashboard/ReviewHistoryTable";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

export default function DashboardPage() {
  const { reviewList, totalReviews, isLoadingList, fetchReviewList } =
    useReviewStore();
  const [riskFilter, setRiskFilter] = useState<string | undefined>(undefined);

  useEffect(() => {
    fetchReviewList(riskFilter);
  }, [fetchReviewList, riskFilter]);

  // Compute risk distribution for chart
  const riskDistribution = [
    {
      level: "HIGH",
      count: reviewList.filter((r) => r.overall_risk_level === "HIGH").length,
      color: "#ef4444",
    },
    {
      level: "MEDIUM",
      count: reviewList.filter((r) => r.overall_risk_level === "MEDIUM").length,
      color: "#f59e0b",
    },
    {
      level: "LOW",
      count: reviewList.filter((r) => r.overall_risk_level === "LOW").length,
      color: "#22c55e",
    },
  ];

  // Stats
  const avgScore =
    reviewList.length > 0
      ? (
          reviewList.reduce((sum, r) => sum + (r.overall_risk_score || 0), 0) /
          reviewList.length
        ).toFixed(1)
      : "—";

  const totalFindings = reviewList.reduce(
    (sum, r) => sum + r.finding_count,
    0
  );

  return (
    <div className="max-w-7xl mx-auto px-6 py-10 page-enter">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-100 mb-1">Dashboard</h1>
        <p className="text-gray-500">
          Review history and risk analytics across all SOW reviews.
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        {[
          {
            label: "Total Reviews",
            value: totalReviews,
            icon: "📋",
            accent: "from-brand-500/10 to-purple-500/10",
          },
          {
            label: "Total Findings",
            value: totalFindings,
            icon: "🔍",
            accent: "from-blue-500/10 to-cyan-500/10",
          },
          {
            label: "Avg Risk Score",
            value: avgScore,
            icon: "📊",
            accent: "from-amber-500/10 to-orange-500/10",
          },
          {
            label: "High Risk",
            value: riskDistribution[0].count,
            icon: "🔴",
            accent: "from-red-500/10 to-rose-500/10",
          },
        ].map((stat, i) => (
          <div
            key={i}
            className={`glass-card p-5 bg-gradient-to-br ${stat.accent}`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-500">{stat.label}</span>
              <span className="text-xl">{stat.icon}</span>
            </div>
            <span className="text-3xl font-bold text-gray-200">
              {stat.value}
            </span>
          </div>
        ))}
      </div>

      {/* Chart + Filters Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Risk Distribution Chart */}
        <div className="glass-card p-6 lg:col-span-2">
          <h2 className="text-lg font-semibold text-gray-200 mb-4">
            Risk Distribution
          </h2>
          {reviewList.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={riskDistribution}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="rgba(255,255,255,0.05)"
                />
                <XAxis
                  dataKey="level"
                  tick={{ fill: "#9ca3af", fontSize: 12 }}
                  axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
                />
                <YAxis
                  tick={{ fill: "#9ca3af", fontSize: 12 }}
                  axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
                  allowDecimals={false}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1e2030",
                    border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: "12px",
                    color: "#e5e7eb",
                  }}
                />
                <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                  {riskDistribution.map((entry, index) => (
                    <Cell key={index} fill={entry.color} fillOpacity={0.8} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[200px] flex items-center justify-center text-gray-600">
              No data to display
            </div>
          )}
        </div>

        {/* Risk Filter */}
        <div className="glass-card p-6">
          <h2 className="text-lg font-semibold text-gray-200 mb-4">
            Filter by Risk
          </h2>
          <div className="space-y-2">
            <button
              onClick={() => setRiskFilter(undefined)}
              className={`w-full text-left px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                !riskFilter
                  ? "bg-brand-500/10 text-brand-400 border border-brand-500/20"
                  : "text-gray-400 hover:bg-white/5 border border-transparent"
              }`}
            >
              All Reviews ({totalReviews})
            </button>
            {(["HIGH", "MEDIUM", "LOW"] as RiskLevel[]).map((level) => {
              const count = riskDistribution.find(
                (r) => r.level === level
              )?.count;
              const colors = {
                HIGH: "text-red-400 bg-red-500/10 border-red-500/20",
                MEDIUM: "text-amber-400 bg-amber-500/10 border-amber-500/20",
                LOW: "text-green-400 bg-green-500/10 border-green-500/20",
              };
              return (
                <button
                  key={level}
                  onClick={() => setRiskFilter(level)}
                  className={`w-full text-left px-4 py-3 rounded-xl text-sm font-medium transition-all border ${
                    riskFilter === level
                      ? colors[level]
                      : "text-gray-400 hover:bg-white/5 border-transparent"
                  }`}
                >
                  {level} ({count})
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Review History Table */}
      <ReviewHistoryTable reviews={reviewList} isLoading={isLoadingList} />
    </div>
  );
}
