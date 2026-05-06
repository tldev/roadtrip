import { Hono } from "hono";
import itineraryData from "../data/itinerary.json" with { type: "json" };
import tripData from "../data/trip.json" with { type: "json" };
import geometriesData from "../data/route-geometries.json" with { type: "json" };
import { attemptLogin, isAdmin, logout, authConfigStatus } from "./auth";
import {
  findSubmission,
  getLatestPing,
  listSubmissions,
  moderateSubmission,
  recordPing,
  recordSubmission,
} from "./db";
import { verifyCaptcha } from "./captcha";
import { clientIp, rateLimit } from "./ratelimit";

type Day = (typeof itineraryData.days)[number];

const app = new Hono();

const VERSION = process.env.GIT_SHA ?? "dev";
const HCAPTCHA_SITEKEY = process.env.HCAPTCHA_SITEKEY ?? "";

app.get("/healthz", (c) =>
  c.json({ status: "ok", version: VERSION, ts: new Date().toISOString() }),
);

// ---- Public read APIs ----

app.get("/api/itinerary", (c) => c.json(itineraryData));
app.get("/api/trip", (c) => c.json(tripData));
app.get("/api/geometries", (c) => c.json(geometriesData));
app.get("/api/config", (c) =>
  c.json({
    hcaptchaSitekey: HCAPTCHA_SITEKEY,
    captchaEnabled: HCAPTCHA_SITEKEY.length > 0,
    auth: authConfigStatus(),
  }),
);

app.get("/api/today", (c) => {
  const today = currentTripDate();
  const days = itineraryData.days as Day[];
  const todayDay = days.find((d) => d.date === today);
  const tomorrow = nextDate(today);
  const tomorrowDay = days.find((d) => d.date === tomorrow);
  return c.json({
    today: todayDay ?? null,
    tomorrow: tomorrowDay ?? null,
    referenceDate: today,
    tripStart: days[0]?.date ?? null,
    tripEnd: days[days.length - 1]?.date ?? null,
  });
});

app.get("/api/location", (c) => {
  const ping = getLatestPing();
  if (!ping) {
    return c.json({ ping: null, message: "Live tracking starts when the trip begins." });
  }
  const minutesAgo = Math.max(0, Math.round((Date.now() - new Date(ping.ts).getTime()) / 60000));
  return c.json({ ping: { ...ping, minutesAgo } });
});

// ---- Admin-gated writes ----

app.post("/api/location", async (c) => {
  if (!(await isAdmin(c))) return c.json({ error: "unauthorized" }, 401);
  const body = await c.req.json().catch(() => null);
  if (!body || typeof body.lat !== "number" || typeof body.lng !== "number") {
    return c.json({ error: "lat and lng are required numbers" }, 400);
  }
  if (Math.abs(body.lat) > 90 || Math.abs(body.lng) > 180) {
    return c.json({ error: "out-of-range coords" }, 400);
  }
  const label = typeof body.label === "string" ? body.label.slice(0, 120) : null;
  const ping = recordPing(body.lat, body.lng, label);
  return c.json({ ping });
});

// ---- Submissions ----

app.post("/api/submissions", async (c) => {
  const ip = clientIp(c);
  if (!rateLimit(`sub:${ip}`, 10, 60_000)) {
    return c.json({ error: "too many submissions, please slow down" }, 429);
  }
  const body = await c.req.json().catch(() => null);
  if (!body) return c.json({ error: "bad json" }, 400);

  const captchaOk = await verifyCaptcha(body.captcha, ip);
  if (!captchaOk) return c.json({ error: "captcha failed" }, 400);

  const name = trimStr(body.name, 120);
  if (!name) return c.json({ error: "name is required" }, 400);

  const sub = recordSubmission({
    name,
    description: trimStr(body.description, 1000),
    url: trimUrl(body.url),
    submitter_name: trimStr(body.submitter_name, 80),
    for_date: trimIsoDate(body.for_date),
    for_stop: trimStr(body.for_stop, 120),
  });
  return c.json({ submission: { id: sub.id, status: sub.status } }, 201);
});

app.get("/api/submissions", async (c) => {
  const status = c.req.query("status") ?? "approved";
  if (status !== "approved" && status !== "pending" && status !== "rejected") {
    return c.json({ error: "invalid status" }, 400);
  }
  if (status !== "approved" && !(await isAdmin(c))) {
    return c.json({ error: "unauthorized" }, 401);
  }
  const subs = listSubmissions(status);
  if (status === "approved") {
    return c.json({ submissions: subs.map(stripPrivate) });
  }
  return c.json({ submissions: subs });
});

// ---- Admin routes ----

app.post("/admin/login", async (c) => {
  const ip = clientIp(c);
  if (!rateLimit(`login:${ip}`, 5, 60_000)) {
    return c.json({ error: "too many attempts" }, 429);
  }
  const body = await c.req.json().catch(() => null);
  const token = typeof body?.token === "string" ? body.token : "";
  const ok = await attemptLogin(c, token);
  return ok ? c.json({ ok: true }) : c.json({ error: "invalid token" }, 401);
});

app.post("/admin/logout", (c) => {
  logout(c);
  return c.json({ ok: true });
});

app.get("/admin/me", async (c) => c.json({ admin: await isAdmin(c) }));

app.post("/admin/submissions/:id", async (c) => {
  if (!(await isAdmin(c))) return c.json({ error: "unauthorized" }, 401);
  const id = Number(c.req.param("id"));
  if (!Number.isInteger(id)) return c.json({ error: "bad id" }, 400);
  const body = await c.req.json().catch(() => null);
  const action = body?.action;
  if (action !== "approve" && action !== "reject") {
    return c.json({ error: "action must be approve or reject" }, 400);
  }
  if (!findSubmission(id)) return c.json({ error: "not found" }, 404);
  const note = trimStr(body?.note, 500);
  const status = action === "approve" ? "approved" : "rejected";
  const updated = moderateSubmission(id, status, note);
  return c.json({ submission: updated });
});

// ---- Static assets ----
//
// scripts/build.ts emits dist/public/<name>.<contenthash>.<ext> for each
// JS/CSS bundle and writes a logical→hashed manifest. We read the manifest
// + HTML templates at boot and substitute the hashed URLs into placeholder
// tokens (__APP_JS__, __APP_CSS__, __ADMIN_JS__, __ADMIN_CSS__). HTML
// goes out no-cache; hashed assets are immutable for a year — new builds
// emit new filenames, so any caching layer treats them as fresh URLs.

const DIST = "./dist/public";
const manifest = (await Bun.file(`${DIST}/manifest.json`).json()) as Record<string, string>;

const indexHtml = (await Bun.file(`${DIST}/index.html`).text())
  .replaceAll("__APP_JS__", manifest["app.js"]!)
  .replaceAll("__APP_CSS__", manifest["app.css"]!);
const adminHtml = (await Bun.file(`${DIST}/admin/index.html`).text())
  .replaceAll("__ADMIN_JS__", manifest["admin/admin.js"]!)
  .replaceAll("__ADMIN_CSS__", manifest["admin/admin.css"]!);

const NO_CACHE = "no-cache, must-revalidate";
const IMMUTABLE = "public, max-age=31536000, immutable";

app.get("/", (c) => c.html(indexHtml, 200, { "cache-control": NO_CACHE }));
app.get("/admin", (c) => c.html(adminHtml, 200, { "cache-control": NO_CACHE }));
app.get("/favicon.svg", () => assetResponse(`${DIST}/favicon.svg`, "image/svg+xml"));
app.get("/favicon.ico", (c) => c.body(null, 204));

app.get("/data/:file", async (c) => {
  const file = c.req.param("file");
  if (!/^[a-zA-Z0-9._-]+\.json$/.test(file)) return c.notFound();
  const path = `./data/${file}`;
  const f = Bun.file(path);
  if (!(await f.exists())) return c.notFound();
  return new Response(f, {
    headers: { "content-type": "application/json", "cache-control": NO_CACHE },
  });
});

// Hashed asset paths: /<name>.<8-hex>.<ext> (top-level or under /admin/).
// Registered last so /data/:file and the API/admin routes match first.
const HASHED_PATTERN = /^\/(?:[a-zA-Z0-9_-]+\/)?[a-zA-Z0-9_-]+\.[0-9a-f]{8}\.(?:js|css)$/;
app.get("/*", async (c) => {
  const path = c.req.path;
  if (!HASHED_PATTERN.test(path)) return c.notFound();
  const ext = path.endsWith(".js") ? "text/javascript; charset=utf-8" : "text/css; charset=utf-8";
  return assetResponse(`${DIST}${path}`, ext);
});

async function assetResponse(path: string, contentType: string): Promise<Response> {
  const f = Bun.file(path);
  if (!(await f.exists())) return new Response("not found", { status: 404 });
  return new Response(f, {
    headers: { "content-type": contentType, "cache-control": IMMUTABLE },
  });
}

// ---- Helpers ----

function currentTripDate(): string {
  const override = process.env.TRIP_DATE_OVERRIDE;
  if (override) return override;
  return new Date().toISOString().slice(0, 10);
}

function nextDate(iso: string): string {
  const d = new Date(iso + "T00:00:00Z");
  d.setUTCDate(d.getUTCDate() + 1);
  return d.toISOString().slice(0, 10);
}

function trimStr(v: unknown, max: number): string | null {
  if (typeof v !== "string") return null;
  const t = v.trim();
  return t.length === 0 ? null : t.slice(0, max);
}

function trimUrl(v: unknown): string | null {
  const s = trimStr(v, 500);
  if (!s) return null;
  try {
    const u = new URL(s);
    if (u.protocol !== "http:" && u.protocol !== "https:") return null;
    return u.toString();
  } catch {
    return null;
  }
}

function trimIsoDate(v: unknown): string | null {
  const s = trimStr(v, 10);
  if (!s) return null;
  return /^\d{4}-\d{2}-\d{2}$/.test(s) ? s : null;
}

function stripPrivate<T extends { reviewer_note: unknown; status: unknown }>(s: T) {
  const { reviewer_note, status, ...rest } = s;
  return rest;
}

const port = Number(process.env.PORT ?? 8080);
console.log(`sabby roadtrip site listening on :${port}`);

export default { port, fetch: app.fetch };
