import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig({
    plugins: [react()],
    build: {
        // CodeMirror is lazy-loaded only on pages that render source code.
        chunkSizeWarningLimit: 600,
    },
    server: {
        port: 5173,
        proxy: {
            "/api": "http://localhost:8000",
        },
    },
});
