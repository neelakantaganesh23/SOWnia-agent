/**
 * Axios API client for SOWnia backend.
 *
 * Provides typed functions for all API endpoints with
 * error handling and request/response interceptors.
 */

import axios, { AxiosError, AxiosInstance } from "axios";
import {
  UploadResponse,
  ReviewStartResponse,
  FullReviewResult,
  ReviewListResponse,
  ApiError,
  UserResponse,
} from "./types";

// API base URL. Default to "" so browser calls are SAME-ORIGIN relative
// paths (e.g. /api/v1/upload). next.config.js rewrites /api/* and /health
// server-side to the in-cluster backend, so the browser never needs to
// resolve the backend host directly. (NEXT_PUBLIC_* is baked at build time;
// hardcoding the cluster host here would break browser requests.)
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "";

// Create Axios instance with defaults
const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 120000, // 2 minutes for long review operations
  headers: {
    "Content-Type": "application/json",
  },
  // Send the httpOnly access_token cookie on same-origin requests.
  withCredentials: true,
});

// ─── Request Interceptor ────────────────────────────────────────────────────

apiClient.interceptors.request.use(
  (config) => {
    // Add request timestamp for latency tracking
    (config as any)._startTime = Date.now();
    return config;
  },
  (error) => Promise.reject(error)
);

// ─── Response Interceptor ───────────────────────────────────────────────────

apiClient.interceptors.response.use(
  (response) => {
    const duration = Date.now() - ((response.config as any)._startTime || 0);
    console.debug(
      `[API] ${response.config.method?.toUpperCase()} ${response.config.url} → ${response.status} (${duration}ms)`
    );
    return response;
  },
  (error: AxiosError<ApiError>) => {
    const status = error.response?.status;
    const detail = error.response?.data?.detail || error.message;
    console.error(`[API Error] ${status}: ${detail}`);

    // Session missing/expired - bounce to login (skip if already there or
    // the request itself was a login/signup attempt, which surfaces its
    // own inline error instead of a redirect).
    if (
      status === 401 &&
      typeof window !== "undefined" &&
      !window.location.pathname.startsWith("/login") &&
      !error.config?.url?.includes("/auth/login") &&
      !error.config?.url?.includes("/auth/signup")
    ) {
      window.location.href = "/login";
    }

    return Promise.reject(error);
  }
);

// ─── API Functions ──────────────────────────────────────────────────────────

/**
 * Upload a SOW document (PDF or DOCX).
 */
export async function uploadFile(
  file: File,
  onProgress?: (progress: number) => void
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post<UploadResponse>("/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (event) => {
      if (event.total && onProgress) {
        onProgress(Math.round((event.loaded * 100) / event.total));
      }
    },
  });

  return response.data;
}

/**
 * Start a multi-agent review for an uploaded file.
 */
export async function startReview(
  fileId: string
): Promise<ReviewStartResponse> {
  const response = await apiClient.post<ReviewStartResponse>("/review", {
    file_id: fileId,
  });
  return response.data;
}

/**
 * Get full review results by review ID.
 */
export async function getResults(
  reviewId: string
): Promise<FullReviewResult> {
  const response = await apiClient.get<FullReviewResult>(
    `/results/${reviewId}`
  );
  return response.data;
}

/**
 * Download PDF report for a review.
 */
export async function downloadPdfReport(reviewId: string): Promise<Blob> {
  const response = await apiClient.get(`/results/${reviewId}/pdf`, {
    responseType: "blob",
  });
  return response.data;
}

/**
 * Download annotated PDF with highlighted findings.
 */
export async function downloadAnnotatedPdf(reviewId: string): Promise<Blob> {
  const response = await apiClient.get(`/results/${reviewId}/annotated-pdf`, {
    responseType: "blob",
  });
  return response.data;
}

/**
 * List all past reviews with optional filtering.
 */
export async function listReviews(params?: {
  risk_level?: string;
  limit?: number;
  offset?: number;
}): Promise<ReviewListResponse> {
  const response = await apiClient.get<ReviewListResponse>("/reviews", {
    params,
  });
  return response.data;
}

/**
 * Delete a review by ID.
 */
export async function deleteReview(
  reviewId: string
): Promise<{ review_id: string; message: string }> {
  const response = await apiClient.delete(`/reviews/${reviewId}`);
  return response.data;
}

/**
 * Check backend health.
 */
export async function checkHealth(): Promise<{
  status: string;
  service: string;
}> {
  const response = await axios.get(`${API_BASE_URL}/health`);
  return response.data;
}

// ─── Auth Functions ──────────────────────────────────────────────────────────

export async function signup(
  email: string,
  password: string,
  fullName?: string
): Promise<UserResponse> {
  const response = await apiClient.post<UserResponse>("/auth/signup", {
    email,
    password,
    full_name: fullName,
  });
  return response.data;
}

export async function login(
  email: string,
  password: string
): Promise<UserResponse> {
  const response = await apiClient.post<UserResponse>("/auth/login", {
    email,
    password,
  });
  return response.data;
}

export async function logout(): Promise<void> {
  await apiClient.post("/auth/logout");
}

export async function fetchCurrentUser(): Promise<UserResponse> {
  const response = await apiClient.get<UserResponse>("/auth/me");
  return response.data;
}

/** Full-page redirect into the backend's Google OAuth flow. */
export function googleLoginUrl(): string {
  return `${API_BASE_URL}/api/v1/auth/google/login`;
}

export default apiClient;
