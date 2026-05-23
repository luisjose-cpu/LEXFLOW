import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  outputFileTracingRoot: path.join(__dirname, "../.."),
  reactStrictMode: true,
  transpilePackages: ["@lexflow/ui", "@lexflow/design-system", "@lexflow/shared", "@lexflow/types"]
};

export default nextConfig;
