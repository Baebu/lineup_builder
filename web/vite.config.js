import { defineConfig } from "vite";

export default defineConfig({
  root: ".",
  build: {
    outDir: "dist",
  },
  server: {
    port: 3000,
    open: true,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/dj": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/guilds": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/bot": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/post": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/schedule": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/sent": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/channels": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/images": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/booking": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/bookings": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/admin": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/health": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/user": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/vrchat": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
