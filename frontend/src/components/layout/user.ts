import { UserRole } from '@/types'

/**
 * User identity display helpers shared by the sidebar and header.
 * Kept in a component-free module so files that export components stay
 * fast-refresh compatible.
 */

/** Derive up to two initials from a user id (handles `dr.sara`, `lhw_02`, …). */
export function getUserInitials(name: string): string {
  const parts = name.trim().split(/[\s._-]+/).filter(Boolean)
  if (parts.length === 0) return '··'
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[1][0]).toUpperCase()
}

/** Soft chip colors per role, used by user identity surfaces. */
export const ROLE_BADGE_STYLES: Record<UserRole, string> = {
  [UserRole.ADMIN]: 'bg-purple-50 text-purple-700 ring-purple-600/20',
  [UserRole.CLINICIAN]: 'bg-teal-50 text-teal-700 ring-teal-600/20',
  [UserRole.LHW]: 'bg-blue-50 text-blue-700 ring-blue-600/20',
  [UserRole.PATIENT]: 'bg-amber-50 text-amber-700 ring-amber-600/20',
}
