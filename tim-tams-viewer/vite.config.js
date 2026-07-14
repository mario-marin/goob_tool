import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/goob_tool/',  // Replace with your GitHub repo name, e.g., '/timestamp-viewer/'
})
