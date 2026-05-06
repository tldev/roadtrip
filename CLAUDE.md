# Sabbatical Roadtrip

Public-facing site for tjohnell's sabbatical road trip (May 8 - June 16, 2026), shipped as a self-contained container.

## Stack

- **Server:** Bun + Hono (`src/server.ts`). Bun-native static file serving for the SPA.
- **Frontend:** Vanilla TS/JS + Leaflet (`src/public/`). No framework. CSS variables drive a per-day color theme keyed off the day's biome.
- **Data:** static JSON (`data/trip.json`, `data/itinerary.json`, `data/route-geometries.json`). SQLite on `/data` will land in slice 2 for location pings + visitor submissions.
- **Image:** multi-stage Dockerfile on `oven/bun:1.3-alpine`, runs as non-root.
- **CI/CD:** GitHub Actions builds and pushes `ghcr.io/tldev/roadtrip:latest` + `:sha-<short>` on every push to `master`. Watchtower on the host pulls `:latest` every 5 min.
- **Deploy contract:** see `DEPLOY.md`.

## Source of truth

The Google Sheet "Sabbatical Road Trip 2026" (id `1Lwavr3xv-YycnB0j5_J-kdBGcBJGopf_NdMSrXgDLqg`) is authoritative for the itinerary. `data/trip.json` and `data/itinerary.json` mirror it. Pull via the Sheets API using a gcloud token (Tom is authenticated as tjohnell@gmail.com with Drive scope).

## Trip overview

Two legs forming a loop from Destin, FL:
- **Leg 1 (Home → first campsite):** Destin → Lafayette → Houston → Fredericksburg → Marfa → Santa Fe → Sedona → San Diego → LA → Cambria
- **Leg 2 (first campsite → home):** Cambria → Carmel-by-the-Sea → Las Vegas → Moab → Parker → Hastings → Little Rock → Destin
- **Daytrips:** Austin (near Houston), Santa Barbara (near LA), Big Sur (near Carmel), Los Altos (near Carmel)

## Data files

- `data/trip.json` — legs, stops (lat/lng/type), daytrips. Used by the map view.
- `data/itinerary.json` — per-day breakdown (date, day#, start, end, drivingHours, daytrip, lodging, isRestDay) generated from the sheet. Used by the today/tomorrow views.
- `data/route-geometries.json` — `{ "trip": { "<legIndex>-<segIndex>": [[lat,lng], ...] } }`, one driving polyline per consecutive-stop pair. Missing geometries can be backfilled via OSRM public demo (`router.project-osrm.org/route/v1/driving/...`).

## Local dev

```sh
bun install
bun run dev                  # http://localhost:8080
TRIP_DATE_OVERRIDE=2026-05-12 bun run dev   # pin "today" for testing
```

## Visitor model

Reads are public. Writes (location pings, submission moderation) are gated by `ADMIN_TOKEN` — exchanged for a signed `HttpOnly`/`Secure`/`SameSite=Lax` cookie on `/admin`. No user accounts; "us" is a single shared role for the family.
