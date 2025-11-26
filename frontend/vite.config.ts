import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    allowedHosts: true,   // <-- allow mọi host
  },
  preview: {
    allowedHosts: true,   // <-- nếu bạn có dùng vite preview / deploy preview
  }
})