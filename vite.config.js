import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
    root: 'src',
    base: "./",
    server: {
        host: 'localhost',
        port: 5173,
    },
    build: {
        outDir: '../build',
        emptyOutDir: true, // also necessary
     }
  }
)
