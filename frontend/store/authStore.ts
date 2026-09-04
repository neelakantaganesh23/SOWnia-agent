/**
 * Zustand store for authentication state.
 *
 * The JWT itself lives in an httpOnly cookie (invisible to JS) - this
 * store only holds the hydrated user profile, fetched via /auth/me.
 */

import { create } from "zustand";
import { UserResponse } from "@/lib/types";
import {
  login as apiLogin,
  signup as apiSignup,
  logout as apiLogout,
  fetchCurrentUser,
} from "@/lib/api";

interface AuthStore {
  user: UserResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  login: (email: string, password: string) => Promise<boolean>;
  signup: (email: string, password: string, fullName?: string) => Promise<boolean>;
  logout: () => Promise<void>;
  fetchMe: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true, // true until the initial fetchMe() resolves
  error: null,

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const user = await apiLogin(email, password);
      set({ user, isAuthenticated: true, isLoading: false });
      return true;
    } catch (err: any) {
      const message = err.response?.data?.detail || err.message || "Login failed";
      set({ error: message, isLoading: false });
      return false;
    }
  },

  signup: async (email, password, fullName) => {
    set({ isLoading: true, error: null });
    try {
      const user = await apiSignup(email, password, fullName);
      set({ user, isAuthenticated: true, isLoading: false });
      return true;
    } catch (err: any) {
      const message = err.response?.data?.detail || err.message || "Signup failed";
      set({ error: message, isLoading: false });
      return false;
    }
  },

  logout: async () => {
    try {
      await apiLogout();
    } finally {
      set({ user: null, isAuthenticated: false });
      window.location.href = "/login";
    }
  },

  fetchMe: async () => {
    set({ isLoading: true });
    try {
      const user = await fetchCurrentUser();
      set({ user, isAuthenticated: true, isLoading: false });
    } catch {
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  clearError: () => set({ error: null }),
}));
