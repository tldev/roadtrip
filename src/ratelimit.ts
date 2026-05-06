import type { Context } from "hono";

type Bucket = number[];

const buckets = new Map<string, Bucket>();
const MAX_TRACKED = 5000;

export function clientIp(c: Context): string {
  const cf = c.req.header("cf-connecting-ip");
  if (cf) return cf;
  const xff = c.req.header("x-forwarded-for");
  if (xff) return xff.split(",")[0]?.trim() ?? "0.0.0.0";
  return "0.0.0.0";
}

export function rateLimit(key: string, limit: number, windowMs: number): boolean {
  const now = Date.now();
  const cutoff = now - windowMs;
  const arr = buckets.get(key);
  const recent = arr ? arr.filter((t) => t > cutoff) : [];
  if (recent.length >= limit) {
    buckets.set(key, recent);
    return false;
  }
  recent.push(now);
  buckets.set(key, recent);
  if (buckets.size > MAX_TRACKED) gc(cutoff);
  return true;
}

function gc(cutoff: number): void {
  for (const [k, v] of buckets) {
    const filtered = v.filter((t) => t > cutoff);
    if (filtered.length === 0) buckets.delete(k);
    else buckets.set(k, filtered);
  }
}
