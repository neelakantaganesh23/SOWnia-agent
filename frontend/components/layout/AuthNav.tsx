"use client";

import { useEffect } from "react";
import { useAuthStore } from "@/store/authStore";

/** Client-side auth-aware slice of the header nav (layout.tsx itself is a
 * server component; zustand auth state is client-only). Also responsible
 * for hydrating the session on first load via GET /auth/me. */
export default function AuthNav() {
  const { user, isAuthenticated, isLoading, fetchMe, logout } = useAuthStore();

  useEffect(() => {
    fetchMe();
  }, [fetchMe]);

  if (isLoading) {
    return <div className="w-16 h-4 rounded skeleton" />;
  }

  if (!isAuthenticated) {
    return (
      <a
        href="/login"
        className="px-4 py-2 rounded-lg text-sm font-medium text-gray-400 hover:text-white hover:bg-white/5 transition-all"
      >
        Log in
      </a>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <span className="text-sm text-gray-400 truncate max-w-[160px]">
        {user?.full_name || user?.email}
      </span>
      <button
        onClick={() => logout()}
        className="px-3 py-1.5 rounded-lg text-xs font-medium text-gray-400 hover:text-white hover:bg-white/5 transition-all"
      >
        Sign out
      </button>
    </div>
  );
}
