/**
 * TypeScript interfaces matching backend Pydantic models.
 * 
 * These types define the data structures used across the frontend
 * for upload, review, and dashboard features.
 */

// ─── Risk & Status Enums ─────────────────────────────────────────────────────

export type RiskLevel = "HIGH" | "MEDIUM" | "LOW";
export type ReviewStatus = "pending" | "in_progress" | "complete" | "error";

// ─── Upload Types ────────────────────────────────────────────────────────────

export interface UploadResponse {
  file_id: string;
  filename: string;
  file_size: number;
  content_type: string;
  page_count: number | null;
  text_length: number;
  message: string;
}

// ─── Review Types ────────────────────────────────────────────────────────────

export interface ReviewStartResponse {
  review_id: string;
  file_id: string;
  status: ReviewStatus;
  message: string;
}

export interface Finding {
  finding: string;
  risk_level: RiskLevel;
  confidence: number;
  page_reference: string | null;
  recommendation: string;
  source_text?: string | null;
  agent?: string;
  domain?: string;
}

export interface AgentResult {
  agent?: string;
  domain?: string;
  findings: Finding[];
  agent_confidence: number;
  error?: string | null;
}

export interface FullReviewResult {
  review_id: string;
  filename: string;
  timestamp: string;
  overall_risk_score: number | null;
  overall_risk_level: RiskLevel | null;
  summary: string | null;
  status: ReviewStatus;
  error: string | null;
  agents: Record<string, AgentResult>;
}

// ─── Dashboard Types ─────────────────────────────────────────────────────────

export interface ReviewListItem {
  review_id: string;
  filename: string;
  timestamp: string;
  overall_risk_score: number | null;
  overall_risk_level: RiskLevel | null;
  status: ReviewStatus;
  finding_count: number;
}

export interface ReviewListResponse {
  reviews: ReviewListItem[];
  total: number;
}

// ─── Agent Card Props ────────────────────────────────────────────────────────

export interface AgentCardProps {
  agent: string;
  domain: string;
  findings: Finding[];
  confidence: number;
  riskLevel: RiskLevel;
}

// ─── Utility Types ───────────────────────────────────────────────────────────

export interface ApiError {
  detail: string;
  error_code?: string;
}

// ─── Auth Types ──────────────────────────────────────────────────────────────

export interface UserResponse {
  id: string;
  email: string;
  full_name: string | null;
}

// Vivid design-handoff risk palette - mirrors tailwind.config.ts's
// colors.risk.{high,medium,low} for contexts (SVG stroke, Recharts fill)
// that need a raw hex rather than a Tailwind class.
export const RISK_COLORS: Record<RiskLevel, string> = {
  HIGH: "#FB4E6D",
  MEDIUM: "#FBBF24",
  LOW: "#34D399",
};

export const RISK_BG_COLORS: Record<RiskLevel, string> = {
  HIGH: "rgba(251, 78, 109, 0.16)",
  MEDIUM: "rgba(251, 191, 36, 0.16)",
  LOW: "rgba(52, 211, 153, 0.16)",
};

export const DOMAIN_LABELS: Record<string, string> = {
  legal: "Legal Review",
  financial: "Financial Review",
  technical: "Technical Review",
  risk: "Risk Assessment",
  delivery: "Delivery Review",
};

// Domain icons live in lib/domainIcons.tsx as lucide-react components
// (kept out of this file since it's plain data/types, not JSX).
