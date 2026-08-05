import { Zap, Target, BarChart3 } from "lucide-react";
import FileUploadZone from "@/components/upload/FileUploadZone";

export default function HomePage() {
  return (
    <div className="min-h-[calc(100vh-8rem)] flex flex-col items-center justify-center px-6 py-20 page-enter">
      {/* Hero Section */}
      <div className="text-center max-w-3xl mx-auto mb-12">
        {/* Decorative badge */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-brand-500/10 border border-brand-500/20 mb-6">
          <div className="w-2 h-2 rounded-full bg-brand-400 animate-pulse-slow" />
          <span className="text-xs font-medium text-brand-400">
            AI-Powered Multi-Agent Review
          </span>
        </div>

        <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight mb-4">
          <span className="gradient-text">Review SOW Documents</span>
          <br />
          <span className="text-gray-200">in Minutes, Not Days</span>
        </h1>

        <p className="text-lg text-gray-400 max-w-xl mx-auto leading-relaxed">
          Upload your Statement of Work and let 5 specialized AI agents review it
          across legal, financial, technical, risk, and delivery domains —
          simultaneously.
        </p>
      </div>

      {/* Upload Zone */}
      <FileUploadZone />

      {/* Features Row */}
      <div className="mt-20 max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          {
            Icon: Zap,
            title: "5 AI Agents",
            desc: "Legal, Financial, Technical, Risk, and Delivery review agents work in parallel.",
          },
          {
            Icon: Target,
            title: "Structured Findings",
            desc: "Each finding includes risk level, confidence score, page reference, and actionable recommendations.",
          },
          {
            Icon: BarChart3,
            title: "Risk Scoring",
            desc: "Weighted overall risk score with executive summary and downloadable PDF report.",
          },
        ].map(({ Icon, title, desc }, i) => (
          <div
            key={i}
            className="glass-card p-6 text-center hover:scale-[1.02] transition-transform duration-200"
          >
            <Icon className="w-8 h-8 mx-auto mb-3 text-accent" strokeWidth={1.75} />
            <h3 className="font-semibold text-gray-200 mb-1.5">{title}</h3>
            <p className="text-sm text-gray-500 leading-relaxed">{desc}</p>
          </div>
        ))}
      </div>

      {/* Background decorative elements */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 -left-32 w-96 h-96 bg-brand-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-purple-500/5 rounded-full blur-3xl" />
      </div>
    </div>
  );
}
