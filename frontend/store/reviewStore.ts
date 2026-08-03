/**
 * Zustand store for SOWnia review state management.
 *
 * Manages: current review data, upload state, review list,
 * loading indicators, and error state.
 */

import { create } from "zustand";
import {
  FullReviewResult,
  ReviewListItem,
  ReviewStatus,
  UploadResponse,
} from "@/lib/types";
import {
  uploadFile,
  startReview,
  getResults,
  listReviews,
} from "@/lib/api";

interface ReviewStore {
  // Upload state
  uploadProgress: number;
  uploadResponse: UploadResponse | null;
  isUploading: boolean;

  // Review state
  currentReview: FullReviewResult | null;
  isReviewing: boolean;
  reviewId: string | null;

  // Dashboard state
  reviewList: ReviewListItem[];
  totalReviews: number;
  isLoadingList: boolean;

  // Error state
  error: string | null;

  // Actions
  uploadDocument: (file: File) => Promise<string | null>;
  startDocumentReview: (fileId: string) => Promise<string | null>;
  pollResults: (reviewId: string) => Promise<void>;
  fetchReviewResults: (reviewId: string) => Promise<void>;
  fetchReviewList: (riskLevel?: string) => Promise<void>;
  clearError: () => void;
  reset: () => void;
}

export const useReviewStore = create<ReviewStore>((set, get) => ({
  // Initial state
  uploadProgress: 0,
  uploadResponse: null,
  isUploading: false,
  currentReview: null,
  isReviewing: false,
  reviewId: null,
  reviewList: [],
  totalReviews: 0,
  isLoadingList: false,
  error: null,

  // ─── Upload Action ──────────────────────────────────────────────────────

  uploadDocument: async (file: File) => {
    set({ isUploading: true, uploadProgress: 0, error: null });
    try {
      const response = await uploadFile(file, (progress) => {
        set({ uploadProgress: progress });
      });
      set({ uploadResponse: response, isUploading: false });
      return response.file_id;
    } catch (err: any) {
      const message =
        err.response?.data?.detail || err.message || "Upload failed";
      set({ error: message, isUploading: false });
      return null;
    }
  },

  // ─── Start Review Action ────────────────────────────────────────────────

  startDocumentReview: async (fileId: string) => {
    set({ isReviewing: true, error: null });
    try {
      const response = await startReview(fileId);
      set({ reviewId: response.review_id });
      return response.review_id;
    } catch (err: any) {
      const message =
        err.response?.data?.detail || err.message || "Failed to start review";
      set({ error: message, isReviewing: false });
      return null;
    }
  },

  // ─── Poll Results Action ────────────────────────────────────────────────

  pollResults: async (reviewId: string) => {
    const poll = async () => {
      try {
        const result = await getResults(reviewId);
        set({ currentReview: result });

        if (
          result.status === "complete" ||
          result.status === "error"
        ) {
          set({ isReviewing: false });
          return;
        }

        // Continue polling every 3 seconds
        await new Promise((resolve) => setTimeout(resolve, 3000));
        await poll();
      } catch (err: any) {
        const message =
          err.response?.data?.detail ||
          err.message ||
          "Failed to fetch results";
        set({ error: message, isReviewing: false });
      }
    };

    await poll();
  },

  // ─── Fetch Results Action ──────────────────────────────────────────────

  fetchReviewResults: async (reviewId: string) => {
    set({ isReviewing: true, error: null });
    try {
      const result = await getResults(reviewId);
      set({ currentReview: result, isReviewing: false, reviewId });
    } catch (err: any) {
      const message =
        err.response?.data?.detail ||
        err.message ||
        "Failed to fetch results";
      set({ error: message, isReviewing: false });
    }
  },

  // ─── Fetch Review List Action ──────────────────────────────────────────

  fetchReviewList: async (riskLevel?: string) => {
    set({ isLoadingList: true, error: null });
    try {
      const response = await listReviews({
        risk_level: riskLevel,
        limit: 50,
      });
      set({
        reviewList: response.reviews,
        totalReviews: response.total,
        isLoadingList: false,
      });
    } catch (err: any) {
      const message =
        err.response?.data?.detail ||
        err.message ||
        "Failed to fetch reviews";
      set({ error: message, isLoadingList: false });
    }
  },

  // ─── Utility Actions ──────────────────────────────────────────────────

  clearError: () => set({ error: null }),

  reset: () =>
    set({
      uploadProgress: 0,
      uploadResponse: null,
      isUploading: false,
      currentReview: null,
      isReviewing: false,
      reviewId: null,
      error: null,
    }),
}));
