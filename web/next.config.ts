import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Cache Components is off: public pages must arrive as complete HTML with a real 404/308 status.
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
