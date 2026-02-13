/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || '',
  },
  // Handle images
  images: {
    domains: ['lh3.googleusercontent.com'],
    unoptimized: true,
  },
}

module.exports = nextConfig
