import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  env: {
    RESOURCE_WALLET_ADDRESS: process.env.RESOURCE_WALLET_ADDRESS,
    NEXT_PUBLIC_FACILITATOR_URL: process.env.NEXT_PUBLIC_FACILITATOR_URL,
  },
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "images.rawpixel.com",
        port: "",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "i.postimg.cc",
        port: "",
        pathname: "/**",
      },
    ],
  },
  experimental: {
    serverComponentsExternalPackages: ["@coinbase/x402", "@coinbase/cdp-sdk"],
  },
  webpack(config, { isServer, nextRuntime }) {
    config.module.rules.push({
      test: /\.svg$/,
      use: ["@svgr/webpack"],
    });

    if (nextRuntime === "edge") {
      config.resolve.alias = {
        ...config.resolve.alias,
        "supports-color": false,
        debug: false,
      };

      config.externals = config.externals || [];
      config.externals.push({
        bufferutil: "bufferutil",
        "utf-8-validate": "utf-8-validate",
      });
    }

    return config;
  },
};

export default nextConfig;
