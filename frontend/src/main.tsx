import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { MotionConfig } from 'motion/react'

import './index.css'
import App from './App'
import { Toaster } from '@/components/ui/sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import { AdminProvider } from '@/hooks/useAdmin'
import { ThemeProvider, useTheme } from '@/hooks/useTheme'

function ThemedToaster() {
  const { resolved } = useTheme()
  return <Toaster theme={resolved} position="bottom-right" richColors closeButton />
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider>
    <MotionConfig reducedMotion="user">
      <TooltipProvider>
        <AdminProvider>
          <App />
        </AdminProvider>
      </TooltipProvider>
    </MotionConfig>
    <ThemedToaster />
    </ThemeProvider>
  </StrictMode>,
)
