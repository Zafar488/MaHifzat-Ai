import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { TOKEN_KEY, loginApi } from '@/lib/api-client'
import type { TokenPayload, UserInfo } from '@/types'

export interface AuthContextValue {
  /** Raw JWT access token, or null when signed out. */
  token: string | null
  /** Identity of the signed-in user ({ user_id, role }), or null. */
  user: UserInfo | null
  /** True when a valid, unexpired token is present. */
  isAuthenticated: boolean
  /** True until the initial session restore from localStorage has finished. */
  isInitializing: boolean
  /** Exchange credentials for a JWT and persist it. Rejects on failure. */
  login: (username: string, password: string) => Promise<void>
  /** Drop credentials and redirect to /login. */
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

/**
 * Decode the base64url payload segment of a JWT into a TokenPayload.
 * Returns null when the token is malformed and cannot be decoded.
 */
function decodeToken(token: string): TokenPayload | null {
  try {
    const payloadPart = token.split('.')[1]
    if (!payloadPart) return null

    // base64url -> base64, then restore stripped '=' padding.
    const base64 = payloadPart.replace(/-/g, '+').replace(/_/g, '/')
    const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), '=')

    // Decode as UTF-8 so non-ASCII claims survive round-tripping.
    const bytes = Uint8Array.from(atob(padded), (char) => char.charCodeAt(0))
    const payload = JSON.parse(new TextDecoder().decode(bytes)) as TokenPayload

    if (typeof payload.sub !== 'string' || typeof payload.role !== 'string') {
      return null
    }
    return payload
  } catch {
    return null
  }
}

/** True when the token's `exp` claim is in the past (or absent — treat as expired). */
function isExpired(payload: TokenPayload): boolean {
  return typeof payload.exp !== 'number' || payload.exp * 1000 <= Date.now()
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null)
  const [user, setUser] = useState<UserInfo | null>(null)
  // Route guards need to tell "signed out" apart from "session not yet restored".
  const [isInitializing, setIsInitializing] = useState(true)

  // On mount, restore the session from localStorage. A token that is
  // malformed or already expired triggers an automatic logout. The `finally`
  // block guarantees `isInitializing` flips to false on every path so
  // ProtectedRoute never bounces a restoring session to /login.
  useEffect(() => {
    try {
      const stored = localStorage.getItem(TOKEN_KEY)
      if (stored) {
        const payload = decodeToken(stored)
        if (payload && !isExpired(payload)) {
          setToken(stored)
          setUser({ user_id: payload.sub, role: payload.role })
        } else {
          localStorage.removeItem(TOKEN_KEY)
        }
      }
    } finally {
      setIsInitializing(false)
    }
  }, [])

  const login = useCallback(async (username: string, password: string) => {
    const { access_token } = await loginApi(username, password)

    const payload = decodeToken(access_token)
    if (!payload) {
      throw new Error('Login succeeded but the returned token is malformed.')
    }
    if (isExpired(payload)) {
      throw new Error('Login succeeded but the returned token is already expired.')
    }

    localStorage.setItem(TOKEN_KEY, access_token)
    setToken(access_token)
    setUser({ user_id: payload.sub, role: payload.role })
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    setToken(null)
    setUser(null)
    window.location.href = '/login'
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      user,
      isAuthenticated: token !== null && user !== null,
      isInitializing,
      login,
      logout,
    }),
    [token, user, isInitializing, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

/** Consume the auth context. Must be used inside an <AuthProvider>. */
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an <AuthProvider>.')
  }
  return context
}
