import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { MotionConfig } from 'motion/react'

import '../index.css'
import Landing from './Landing'
import { TooltipProvider } from '@/components/ui/tooltip'
import { ThemeProvider } from '@/hooks/useTheme'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider>
      <MotionConfig reducedMotion="user">
        <TooltipProvider>
          <Landing />
        </TooltipProvider>
      </MotionConfig>
    </ThemeProvider>
  </StrictMode>,
)
