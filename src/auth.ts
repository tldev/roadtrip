import type { Context } from "hono";
import { deleteCookie, getSignedCookie, setSignedCookie } from "hono/cookie";

const COOKIE_NAME = "sabby_admin";
const COOKIE_VALUE = "admin";
const THIRTY_DAYS = 60 * 60 * 24 * 30;

function adminToken(): string | null {
  return process.env.ADMIN_TOKEN ?? null;
}

function cookieSecret(): string | null {
  const s = process.env.COOKIE_SECRET;
  return s && s.length >= 32 ? s : null;
}

function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let r = 0;
  for (let i = 0; i < a.length; i++) r |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return r === 0;
}

export async function isAdmin(c: Context): Promise<boolean> {
  const auth = c.req.header("authorization");
  if (auth?.startsWith("Bearer ")) {
    const token = auth.slice(7).trim();
    const expected = adminToken();
    if (expected && timingSafeEqual(token, expected)) return true;
  }
  const secret = cookieSecret();
  if (!secret) return false;
  try {
    const v = await getSignedCookie(c, secret, COOKIE_NAME);
    return v === COOKIE_VALUE;
  } catch {
    return false;
  }
}

export async function attemptLogin(c: Context, token: string): Promise<boolean> {
  const expected = adminToken();
  const secret = cookieSecret();
  if (!expected || !secret) return false;
  if (!timingSafeEqual(token, expected)) return false;
  await setSignedCookie(c, COOKIE_NAME, COOKIE_VALUE, secret, {
    httpOnly: true,
    secure: isSecureRequest(c),
    sameSite: "Lax",
    maxAge: THIRTY_DAYS,
    path: "/",
  });
  return true;
}

function isSecureRequest(c: Context): boolean {
  const proto = c.req.header("x-forwarded-proto");
  if (proto === "https") return true;
  try {
    return new URL(c.req.url).protocol === "https:";
  } catch {
    return false;
  }
}

export function logout(c: Context): void {
  deleteCookie(c, COOKIE_NAME, { path: "/" });
}

export function authConfigStatus(): { hasToken: boolean; hasSecret: boolean } {
  return { hasToken: adminToken() !== null, hasSecret: cookieSecret() !== null };
}
