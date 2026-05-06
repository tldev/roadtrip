import { Hono } from "hono";
import { serveStatic } from "hono/bun";
import itineraryData from "../data/itinerary.json" with { type: "json" };
import tripData from "../data/trip.json" with { type: "json" };
import geometriesData from "../data/route-geometries.json" with { type: "json" };

type Day = (typeof itineraryData.days)[number];

const app = new Hono();

const VERSION = process.env.GIT_SHA ?? "dev";

app.get("/healthz", (c) =>
  c.json({ status: "ok", version: VERSION, ts: new Date().toISOString() }),
);

app.get("/api/itinerary", (c) => c.json(itineraryData));
app.get("/api/trip", (c) => c.json(tripData));
app.get("/api/geometries", (c) => c.json(geometriesData));

// Slice 1 stub — slice 2 will write/serve real pings from SQLite.
app.get("/api/location", (c) =>
  c.json({ ping: null, message: "Live tracking starts when the trip begins." }),
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
  });
});

app.use("/static/*", serveStatic({ root: "./" }));
app.get("/", serveStatic({ path: "./src/public/index.html" }));
app.get("/app.js", serveStatic({ path: "./src/public/app.js" }));
app.get("/app.css", serveStatic({ path: "./src/public/app.css" }));
app.get("/data/:file", async (c) => {
  const file = c.req.param("file");
  if (!/^[a-zA-Z0-9._-]+\.json$/.test(file)) return c.notFound();
  const path = `./data/${file}`;
  const f = Bun.file(path);
  if (!(await f.exists())) return c.notFound();
  return new Response(f, { headers: { "content-type": "application/json" } });
});

function currentTripDate(): string {
  const override = process.env.TRIP_DATE_OVERRIDE;
  if (override) return override;
  const now = new Date();
  return now.toISOString().slice(0, 10);
}

function nextDate(iso: string): string {
  const d = new Date(iso + "T00:00:00Z");
  d.setUTCDate(d.getUTCDate() + 1);
  return d.toISOString().slice(0, 10);
}

const port = Number(process.env.PORT ?? 8080);
console.log(`sabby roadtrip site listening on :${port}`);

export default { port, fetch: app.fetch };
