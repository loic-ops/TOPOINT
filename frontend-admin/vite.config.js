import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: process.env.VITE_BASE_PATH || "/admin/",
  server: {
    host: "0.0.0.0",
    port: 5174,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on("proxyReq", (proxyReq, req) => {
            // Injecter la vraie IP du client dans X-Forwarded-For
            const clientIp = req.socket.remoteAddress?.replace(/^::ffff:/, "") || "unknown";
            proxyReq.setHeader("X-Forwarded-For", clientIp);
          });
        },
      },
    },
  },
});
