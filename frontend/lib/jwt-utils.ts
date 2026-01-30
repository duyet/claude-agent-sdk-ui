/**
 * JWT Utilities for Token Creation and Management
 *
 * Provides common JWT functionality used by auth routes.
 * Uses JWT_SECRET directly (must match backend).
 */

import { createHash } from "node:crypto"
import { SignJWT } from "jose"
import { v4 as uuidv4 } from "uuid"

/**
 * JWT configuration (must match backend)
 */
export const JWT_CONFIG = {
  algorithm: "HS256" as const,
  accessTokenExpireMinutes: 30,
  refreshTokenExpireDays: 7,
  issuer: "claude-agent-sdk",
  audience: "claude-agent-sdk-users",
}

/**
 * Get JWT secret from environment
 */
export function getJwtSecret(): string {
  const secret = process.env.JWT_SECRET
  if (!secret) {
    throw new Error("JWT_SECRET environment variable not configured")
  }
  return secret
}

/**
 * Derive user ID from API key (same logic as backend)
 */
export function getUserIdFromApiKey(apiKey: string): string {
  return createHash("sha256").update(apiKey).digest("hex").substring(0, 32)
}

/**
 * Create a JWT token
 */
export async function createToken(
  secret: Uint8Array,
  userId: string,
  type: "access" | "refresh" | "user_identity",
  expiresIn: number,
  additionalClaims?: Record<string, string>,
): Promise<{ token: string; jti: string; expiresIn: number }> {
  const jti = uuidv4()
  const now = Math.floor(Date.now() / 1000)
  const exp = now + expiresIn

  const token = await new SignJWT({
    sub: userId,
    jti,
    type,
    ...additionalClaims,
  })
    .setProtectedHeader({ alg: JWT_CONFIG.algorithm, typ: "JWT" })
    .setIssuedAt(now)
    .setExpirationTime(exp)
    .setIssuer(JWT_CONFIG.issuer)
    .setAudience(JWT_CONFIG.audience)
    .sign(secret)

  return { token, jti, expiresIn }
}

/**
 * Get access token expiry in seconds
 */
export function getAccessTokenExpiry(): number {
  return JWT_CONFIG.accessTokenExpireMinutes * 60
}

/**
 * Get refresh token expiry in seconds
 */
export function getRefreshTokenExpiry(): number {
  return JWT_CONFIG.refreshTokenExpireDays * 24 * 60 * 60
}
