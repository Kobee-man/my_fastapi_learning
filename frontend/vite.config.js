import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      '/ws': {
        target: 'ws://127.0.0.1:8000',
        ws: true
      }
    },
    watch: {
      include: ['src/**/*'],
      exclude: [
        'node_modules/**',
        'dist/**',
        '.git/**',
        '*.log'
      ],
      usePolling: true,
      interval: 100
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
})
