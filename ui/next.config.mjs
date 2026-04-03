/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    BACKEND_URL: process.env.BACKEND_URL || "http://127.0.0.1:8081",
  },
};

export default nextConfig;
