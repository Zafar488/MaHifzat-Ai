import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from '@/contexts/AuthContext'
import { queryClient } from '@/lib/query-client'
import { router } from '@/routes'
import { ToastContainer } from '@/components/ui'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    </AuthProvider>
    {/* Global toast notifications — mounted once at the app root. */}
    <ToastContainer />
  </StrictMode>,
)
