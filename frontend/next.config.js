/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  async rewrites() {
    // SERVER-SIDE proxy target. BACKEND_INTERNAL_URL has NO NEXT_PUBLIC_
    // prefix on purpose: it must stay hidden from the browser so client code
    // keeps calling relative /api (same-origin), which keeps the auth cookie
    // first-party. On Vercel set BACKEND_INTERNAL_URL to the Render backend
    // URL; locally it defaults to the dev backend on localhost:8000.
    const backend = process.env.BACKEND_INTERNAL_URL || "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${backend}/api/:path*`,
      },
      {
        source: "/health",
        destination: `${backend}/health`,
      },
    ];
  },
};

module.exports = nextConfig;
