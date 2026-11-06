import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import App from './App.tsx'
import { Toaster } from 'sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import { AuthProvider } from './context/AuthContext'
import { MotionConfig } from 'motion/react'
import { installFx } from './lib/fx'

installFx()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <TooltipProvider delayDuration={200}>
          <MotionConfig reducedMotion="user">
            <App />
          </MotionConfig>
          <Toaster
            position="top-center"
            toastOptions={{
              className: 'font-body !rounded-2xl !border-line !text-ink',
            }}
          />
        </TooltipProvider>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)
