import type { Metadata } from "next";
import Link from "next/link";
import AuthNav from "@/components/layout/AuthNav";
import "./globals.css";

export const metadata: Metadata = {
  title: "SOWnia — AI-Powered SOW Review",
  description:
    "Replace multi-expert, multi-day SOW review cycles with an automated, AI-powered pipeline completed in minutes.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen flex flex-col">
        {/* Navigation Header */}
        <header className="sticky top-0 z-50 w-full border-b border-gray-200/10 bg-surface-950/80 backdrop-blur-xl">
          <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
            {/* Logo */}
            <Link href="/" className="flex items-center gap-3 group">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center shadow-lg shadow-brand-500/20 group-hover:shadow-brand-500/40 transition-shadow">
                <span className="text-white font-bold text-lg">S</span>
              </div>
              <span className="text-xl font-bold gradient-text">SOWnia</span>
            </Link>

            {/* Navigation */}
            <nav className="flex items-center gap-1">
              <Link
                href="/"
                className="px-4 py-2 rounded-lg text-sm font-medium text-gray-400 hover:text-white hover:bg-white/5 transition-all"
              >
                Upload
              </Link>
              <Link
                href="/dashboard"
                className="px-4 py-2 rounded-lg text-sm font-medium text-gray-400 hover:text-white hover:bg-white/5 transition-all"
              >
                Dashboard
              </Link>
              <div className="ml-3 w-px h-6 bg-gray-700" />
              <div className="ml-3 flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse-slow" />
                <span className="text-xs text-gray-500">API Connected</span>
              </div>
              <div className="ml-3 w-px h-6 bg-gray-700" />
              <AuthNav />
            </nav>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1">{children}</main>

        {/* Footer */}
        <footer className="border-t border-gray-200/10 py-6">
          <div className="max-w-7xl mx-auto px-6 flex items-center justify-between text-sm text-gray-500">
            <span>© 2026 SOWnia. AI-Powered SOW Review.</span>
            <span className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-brand-500" />
              v1.0.0
            </span>
          </div>
        </footer>
      </body>
    </html>
  );
}
