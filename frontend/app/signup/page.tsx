"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import { googleLoginUrl } from "@/lib/api";

export default function SignupPage() {
  const router = useRouter();
  const { signup, isLoading, error, clearError } = useAuthStore();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    clearError();
    const ok = await signup(email, password, fullName || undefined);
    if (ok) {
      router.push("/");
    }
  }

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-6">
      <div className="glass-card w-full max-w-[440px] p-10">
        <h1 className="text-2xl font-bold mb-1">Create your account</h1>
        <p className="text-sm text-gray-400 mb-6">
          Start reviewing SOW documents with AI in minutes.
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
            <label className="block text-sm text-gray-400 mb-1" htmlFor="fullName">
              Full name (optional)
            </label>
            <input
              id="fullName"
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full rounded-xl bg-surface-800 border border-gray-700 px-4 py-2.5 text-sm focus:outline-none focus:border-brand-400"
            />
          </div>
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
              minLength={8}
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
            {isLoading ? "Creating account..." : "Create account"}
          </button>
        </form>

        <p className="text-center text-sm text-gray-500 mt-6">
          Already have an account?{" "}
          <Link href="/login" className="text-brand-400 hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
