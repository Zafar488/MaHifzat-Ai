/**
 * Authentication types mirroring `backend/schemas/auth.py`.
 *
 * Note: this project compiles with TypeScript 6's `erasableSyntaxOnly`
 * (no runtime code from TS-only syntax), which disallows `enum`.
 * `UserRole` therefore uses the equivalent erasable const-object +
 * union-type pattern — call sites behave exactly like a string enum:
 * `UserRole.CLINICIAN === 'clinician'`.
 */
export const UserRole = {
  PATIENT: 'patient',
  LHW: 'lhw',
  CLINICIAN: 'clinician',
  ADMIN: 'admin',
} as const

export type UserRole = (typeof UserRole)[keyof typeof UserRole]

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface TokenPayload {
  sub: string
  role: UserRole
  exp: number
}

export interface UserInfo {
  user_id: string
  role: UserRole
}
