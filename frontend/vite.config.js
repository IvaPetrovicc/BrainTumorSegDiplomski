import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const target = env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8000'

  const proxy = {
    '/api': {
      target,
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, ''),
    },
  }

  return {
    plugins: [vue()],
    server: {
      host: '0.0.0.0',
      port: 5174,
      proxy,
    },
    preview: {
      host: '0.0.0.0',
      port: 5174,
      proxy,
    },
  }
})
