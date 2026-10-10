import axios from 'axios'
import type { TokenResponse } from '@/types/auth'

/** localStorage key used to persist the JWT access token. */
export const TOKEN_KEY = 'maahifazat_token'

/**
 * Shared Axios instance for all API requests.
 * Base URL `/api` is proxied to the FastAPI backend (http://localhost:8000)
 * by the Vite dev server, so callers use paths like `/patients` or `/auth/login`.
 */
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
})

// Attach the stored JWT (if any) to every outgoing request.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Session-expiry handling: on a 401 (except from the login endpoint itself,
// where 401 simply means "wrong credentials"), clear the token and force a
// redirect to the login page.
api.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      const isLoginRequest = error.config?.url?.includes('/auth/login') ?? false
      if (!isLoginRequest) {
        localStorage.removeItem(TOKEN_KEY)
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  },
)

/**
 * Exchange username/password credentials for a JWT access token.
 *
 * The backend expects OAuth2 form-encoded data at POST /api/auth/login
 * (FastAPI's `OAuth2PasswordRequestForm`), so the body is sent as
 * URLSearchParams with `application/x-www-form-urlencoded` content type.
 */
export async function loginApi(username: string, password: string): Promise<TokenResponse> {
  const body = new URLSearchParams({ username, password })
  const response = await api.post<TokenResponse>('/auth/login', body, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return response.data
}
