"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import { googleLoginUrl } from "@/lib/api";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, isLoading, error, clearError } = useAuthStore();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    clearError();
    const ok = await login(email, password);
    if (ok) {
      router.push(searchParams.get("next") || "/");
    }
  }

  return (
    <div className="glass-card w-full max-w-[440px] p-10">
      <h1 className="text-2xl font-bold mb-1">Welcome back</h1>
      <p className="text-sm text-gray-400 mb-6">
        Sign in to review your SOW documents.
      </p>

      <a
        href={googleLoginUrl()}
        className="btn-secondary w-full justify-center mb-4"
      >
        Continue with Google
      </a>

      <div className="flex items-center gap-3 my-4">
        <div className="h-px flex-1 bg-gray-700" />
        <span className="text-xs text-gray-500">OR</span>
        <div className="h-px flex-1 bg-gray-700" />
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm text-gray-400 mb-1" htmlFor="email">
            Email
          </label>
          <input
            id="email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-xl bg-surface-800 border border-gray-700 px-4 py-2.5 text-sm focus:outline-none focus:border-brand-400"
          />
        </div>
        <div>
          <label className="block text-sm text-gray-400 mb-1" htmlFor="password">
            Password
          </label>
          <input
            id="password"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-xl bg-surface-800 border border-gray-700 px-4 py-2.5 text-sm focus:outline-none focus:border-brand-400"
          />
        </div>

        {error && <p className="text-sm text-risk-high">{error}</p>}

        <button
          type="submit"
          disabled={isLoading}
          className="btn-primary w-full justify-center disabled:opacity-50"
        >
          {isLoading ? "Signing in..." : "Sign in & review"}
        </button>
      </form>

      <p className="text-center text-sm text-gray-500 mt-6">
        Don&apos;t have an account?{" "}
        <Link href="/signup" className="text-brand-400 hover:underline">
          Sign up
        </Link>
      </p>
    </div>
  );
}

export default function LoginPage() {
  return (
    <div className="min-h-[80vh] flex items-center justify-center px-6">
      <Suspense fallback={<div className="glass-card w-full max-w-[440px] p-10 h-[420px] skeleton" />}>
        <LoginForm />
      </Suspense>
    </div>
  );
}
