import { Suspense, useEffect, useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import { Header } from './Header'
import { Sidebar } from './Sidebar'

/** In-shell fallback while a lazy page chunk is being fetched. */
function PageFallback() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3">
      <Loader2 className="size-6 animate-spin text-teal-600" aria-hidden="true" />
      <p className="font-mono text-[11px] uppercase tracking-[0.3em] text-gray-400">Loading</p>
    </div>
  )
}

/**
 * Authenticated application shell: sidebar (left) + header and scrollable
 * content area (right). Owns the responsive sidebar state — a mobile drawer
 * with a hamburger toggle, and a desktop collapse-to-icons toggle.
 */
export function AppShell() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()

  const [prevPathname, setPrevPathname] = useState(location.pathname)
  if (location.pathname !== prevPathname) {
    setPrevPathname(location.pathname)
    setMobileOpen(false)
  }

  // Escape closes the mobile drawer.
  useEffect(() => {
    if (!mobileOpen) return
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setMobileOpen(false)
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [mobileOpen])

  return (
    <div className="flex h-dvh overflow-hidden bg-white">
      <Sidebar
        mobileOpen={mobileOpen}
        onMobileClose={() => setMobileOpen(false)}
        collapsed={collapsed}
        onToggleCollapsed={() => setCollapsed((value) => !value)}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <Header onMenuClick={() => setMobileOpen((open) => !open)} />
        <main className="app-canvas flex-1 overflow-y-auto focus:outline-none" id="main">
          <Suspense fallback={<PageFallback />}>
            <Outlet />
          </Suspense>
        </main>
      </div>
    </div>
  )
}
