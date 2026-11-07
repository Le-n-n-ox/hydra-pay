import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig, type Plugin } from 'vite'

// Built into ../static so Flask (dashboard.py) serves it on port 8000.
// `npm run dev` proxies the API to a running dashboard.py.
const flask = 'http://127.0.0.1:8000'

// Serve /dashboard (no .html) in dev and preview, matching the Flask route.
const dashboardRoute = (): Plugin => {
  const rewrite = (req: { url?: string }, _res: unknown, next: () => void) => {
    if (req.url === '/dashboard' || req.url?.startsWith('/dashboard?') || req.url?.startsWith('/dashboard#')) req.url = req.url.replace('/dashboard', '/dashboard.html')
    next()
  }
  return { name: 'dashboard-route', configureServer: (s) => void s.middlewares.use(rewrite), configurePreviewServer: (s) => void s.middlewares.use(rewrite) }
}

export default defineConfig({
  plugins: [react(), tailwindcss(), dashboardRoute()],
  resolve: { alias: { '@': path.resolve(import.meta.dirname, './src') } },
  build: {
    outDir: '../static',
    emptyOutDir: true,
    chunkSizeWarningLimit: 1200,
    // Two pages: the public landing page (index.html -> /) and the dashboard (dashboard.html -> /dashboard).
    rollupOptions: { input: { landing: path.resolve(import.meta.dirname, 'index.html'), dashboard: path.resolve(import.meta.dirname, 'dashboard.html') } },
  },
  server: { proxy: { '/api': flask, '/login': flask } },
})
