# Sabbatical Roadtrip Planner

Planning tool for tjohnell's sabbatical road trip (May 8 - June 16, 2026).

## Project Structure

- `data/trip.json` -- Route data: legs, stops, daytrips
- `data/route-geometries.json` -- Driving polylines per leg/segment, keyed `<legIndex>-<segIndex>`
- `serve.sh` -- Dev server (python3, port 8090)

## Source of truth

The Google Sheet "Sabbatical Road Trip 2026" (id `1Lwavr3xv-YycnB0j5_J-kdBGcBJGopf_NdMSrXgDLqg`) is authoritative for the itinerary. `data/trip.json` mirrors it. Pull via the Sheets API using a gcloud token (Tom is authenticated as tjohnell@gmail.com with Drive scope).

## Trip Overview

Two legs forming a loop from Destin, FL:
- **Leg 1 (Home to First Campsite):** Destin -> Lafayette -> Houston -> Fredericksburg -> Marfa -> Santa Fe -> Sedona -> San Diego -> LA -> Cambria
- **Leg 2 (First Campsite to Home):** Cambria -> Carmel-by-the-Sea -> Las Vegas -> Moab -> Parker -> Hastings -> Little Rock -> Destin
- **Daytrips:** Austin (near Houston), Santa Barbara (near LA), Big Sur (near Carmel), Los Altos (near Carmel)

## Data Format

`data/trip.json` stops have lat/lng coordinates and types (start/stop/end). `data/route-geometries.json` has shape `{ "trip": { "<legIndex>-<segIndex>": [[lat,lng], ...] } }` -- one polyline per consecutive stop pair. Missing geometries can be backfilled via the OSRM public demo (`router.project-osrm.org/route/v1/driving/...`).

## Website

The previous static map (`index.html`, `routes.html`, plus attraction/proposal data) was retired on 2026-05-06. A new website is being built from scratch.
