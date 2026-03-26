# Sabbatical Roadtrip Planner

Planning tool for tjohnell's sabbatical road trip (May 9 - June 14, 2026).

## Project Structure

- `data/trip.json` -- All route data: legs, stops, daytrips, brainstorm ideas
- `index.html` -- Interactive map visualization (Leaflet + dark CARTO tiles)
- `serve.sh` -- Dev server (python3, port 8090)

## Trip Overview

Two legs forming a loop from Destin, FL:
- **Leg 1 (Home to First Campsite):** Destin -> Baton Rouge -> Houston -> Fredericksburg -> Fort Davis -> Santa Fe -> Flagstaff -> San Diego -> LA -> Cambria
- **Leg 2 (First Campsite to Home):** Cambria -> Carmel-by-the-Sea -> Las Vegas -> Page -> Silverton -> Parker -> Hastings -> Little Rock -> Destin
- **Daytrips:** Santa Barbara, Big Sur, Los Altos, Boulder, Austin

The leg from Carmel-by-the-Sea to Parker, CO is not finalized -- brainstorming is active for this segment.

## Data Format

All route data lives in `data/trip.json`. Stops have lat/lng coordinates, types (start/stop/end), and optional `finalized: false` for unconfirmed stops. The `ideas` array stores brainstorm entries for route alternatives.

## Visualization

Run `./serve.sh` and open http://localhost:8090. Dark-themed map with:
- Solid lines for planned legs, dashed for draft legs
- Color-coded stops (green=start, red=end, blue/orange=waypoints)
- Diamond markers for daytrips
- Collapsible sidebar with stop lists
