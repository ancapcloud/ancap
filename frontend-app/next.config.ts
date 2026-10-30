import type { NextConfig } from "next";

const securityHeaders = [
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  {
    key: "Permissions-Policy",
    // MoonPay Commerce / Helio checkout may use Payment Request for card rails.
    value: 'camera=(), microphone=(), geolocation=(), payment=(self "https://embed.hel.io" "https://buy.moonpay.com")',
  },
  {
    key: "Content-Security-Policy",
    value: [
      "default-src 'self'",
      "base-uri 'self'",
      "frame-ancestors 'none'",
      "object-src 'none'",
      "img-src 'self' data: blob: https:",
      "font-src 'self' data:",
      "style-src 'self' 'unsafe-inline'",
      "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://challenges.cloudflare.com https://embed.hel.io https://*.hel.io https://*.moonpay.com",
      // http://127.0.0.1:* / localhost:* keep local + GitHub E2E (API on :8001) unblocked;
      // production browsers still talk HTTPS (covered by https:).
      "connect-src 'self' https: wss: http://127.0.0.1:* http://localhost:* ws://127.0.0.1:* ws://localhost:*",
      "frame-src https://challenges.cloudflare.com https://embed.hel.io https://*.hel.io https://*.moonpay.com https://buy.moonpay.com",
      "child-src https://embed.hel.io https://*.hel.io https://*.moonpay.com",
    ].join("; "),
  },
];

const nextConfig: NextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@heliofi/checkout-react", "@metamask/connect-evm", "@metamask/connect-multichain"],
  // Avoid one slow SSR page (e.g. tokenomics RPC) killing the whole Docker build.
  staticPageGenerationTimeout: 180,
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
  async redirects() {
    return [
      { source: "/w", destination: "/", permanent: true },
      { source: "/w/", destination: "/", permanent: true },
      { source: "/w/:path+", destination: "/:path+", permanent: true },
      // Common aliases / legacy paths used in listings and old links
      { source: "/tokenomics", destination: "/acp-supply", permanent: true },
      { source: "/proof", destination: "/proof-center", permanent: true },
      { source: "/market", destination: "/markets", permanent: true },
    ];
  },
  // Fresh Docker builds get new chunk filenames.
  generateBuildId: async () => {
    if (process.env.NODE_ENV === "development") return "development";
    return process.env.NEXT_BUILD_ID || `local-${Date.now()}`;
  },
  // App Router: RSC prefetch from a public hostname (Cloudflare Tunnel) to local dev must be allowed.
  allowedDevOrigins: [
    "https://ancap.cloud",
    "https://www.ancap.cloud",
    "http://ancap.cloud",
    "http://www.ancap.cloud",
  ],
  async rewrites() {
    if (process.env.NODE_ENV !== "development") return [];

    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8001/:path*",
      },
      // Swagger UI (same paths as prod nginx: /api → backend, /openapi.json for spec)
      { source: "/api/docs", destination: "http://127.0.0.1:8001/docs" },
      { source: "/api/redoc", destination: "http://127.0.0.1:8001/redoc" },
      { source: "/openapi.json", destination: "http://127.0.0.1:8001/openapi.json" },
    ];
  },
};

export default nextConfig;
