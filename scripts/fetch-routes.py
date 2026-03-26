#!/usr/bin/env python3
"""
Fetch real road geometries for all trip legs and route proposals.
Outputs data/route-geometries.json for the map UI.

Uses the Valhalla routing engine (OSM-based, free, no API key).
Falls back to OSRM demo server if Valhalla fails.

Usage: python3 scripts/fetch-routes.py

Rate limited to 1 request/second (free public servers).
"""

import json
import time
import urllib.request
import urllib.error
import urllib.parse

VALHALLA_BASE = "https://valhalla1.openstreetmap.de/route"
OSRM_BASE = "https://router.project-osrm.org/route/v1/driving"
RATE_LIMIT = 1.0  # seconds between requests
DATA_DIR = "data"


def decode_polyline(encoded, precision=6):
    """Decode Google encoded polyline. Returns list of [lat, lng]."""
    inv = 10**-precision
    decoded = []
    lat = lng = 0
    i = 0
    while i < len(encoded):
        # Decode latitude
        shift = result = 0
        while True:
            b = ord(encoded[i]) - 63
            i += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        lat += (~(result >> 1) if result & 1 else result >> 1)

        # Decode longitude
        shift = result = 0
        while True:
            b = ord(encoded[i]) - 63
            i += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        lng += (~(result >> 1) if result & 1 else result >> 1)

        decoded.append([lat * inv, lng * inv])
    return decoded


def fetch_valhalla(lat1, lng1, lat2, lng2):
    """Fetch road geometry from Valhalla. Returns list of [lat, lng]."""
    params = json.dumps({
        "locations": [
            {"lat": lat1, "lon": lng1},
            {"lat": lat2, "lon": lng2},
        ],
        "costing": "auto",
    })
    url = f"{VALHALLA_BASE}?json={urllib.parse.quote(params)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SabbyRoadtrip/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            shape = data.get("trip", {}).get("legs", [{}])[0].get("shape", "")
            if not shape:
                return None
            return decode_polyline(shape, precision=6)
    except Exception as e:
        return None


def fetch_osrm(lat1, lng1, lat2, lng2):
    """Fetch road geometry from OSRM. Returns list of [lat, lng]."""
    url = f"{OSRM_BASE}/{lng1},{lat1};{lng2},{lat2}?overview=full&geometries=geojson"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SabbyRoadtrip/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            if data.get("code") != "Ok" or not data.get("routes"):
                return None
            coords = data["routes"][0]["geometry"]["coordinates"]
            return [[c[1], c[0]] for c in coords]  # swap [lng,lat] to [lat,lng]
    except Exception:
        return None


def fetch_route(lat1, lng1, lat2, lng2):
    """Try Valhalla first, fall back to OSRM."""
    coords = fetch_valhalla(lat1, lng1, lat2, lng2)
    if coords:
        return coords
    return fetch_osrm(lat1, lng1, lat2, lng2)


def main():
    with open(f"{DATA_DIR}/trip.json") as f:
        trip = json.load(f)
    with open(f"{DATA_DIR}/route-proposals.json") as f:
        proposals = json.load(f)

    geometries = {"trip": {}, "proposals": {}}
    total = 0
    errors = 0

    # Count total segments
    trip_count = sum(len(leg["stops"]) - 1 for leg in trip["legs"])
    prop_count = sum(
        1 for r in proposals["routes"] for d in r["days"] if d["driving_hours"] > 0
    )
    grand_total = trip_count + prop_count
    print(f"Fetching {grand_total} route segments ({trip_count} trip + {prop_count} proposals)")
    print(f"Estimated time: ~{grand_total * 2} seconds\n")

    # Fetch trip leg segments
    for li, leg in enumerate(trip["legs"]):
        print(f"Leg {li}: {leg['name']}")
        stops = leg["stops"]
        for si in range(len(stops) - 1):
            a, b = stops[si], stops[si + 1]
            key = f"{li}-{si}"
            total += 1
            print(f"  [{total}/{grand_total}] {a['name']} → {b['name']}...", end=" ", flush=True)

            coords = fetch_route(a["lat"], a["lng"], b["lat"], b["lng"])
            if coords:
                geometries["trip"][key] = coords
                print(f"OK ({len(coords)} points)")
            else:
                errors += 1
                print("FAILED — will use straight line")

            if total < grand_total:
                time.sleep(RATE_LIMIT)

    print()

    # Fetch proposal route segments
    for route in proposals["routes"]:
        print(f"Route {route['id']}: {route['name']}")
        for day in route["days"]:
            if day["driving_hours"] <= 0:
                continue
            key = f"{route['id']}-{day['day']}"
            total += 1
            sc = day["start_coords"]
            ec = day["end_coords"]
            print(f"  [{total}/{grand_total}] Day {day['day']}: {day['start']} → {day['end']}...", end=" ", flush=True)

            coords = fetch_route(sc[0], sc[1], ec[0], ec[1])
            if coords:
                geometries["proposals"][key] = coords
                print(f"OK ({len(coords)} points)")
            else:
                errors += 1
                print("FAILED — will use straight line")

            if total < grand_total:
                time.sleep(RATE_LIMIT)

    # Save
    outpath = f"{DATA_DIR}/route-geometries.json"
    with open(outpath, "w") as f:
        json.dump(geometries, f)

    size_mb = len(json.dumps(geometries)) / 1024 / 1024
    print(f"\nDone! {total - errors}/{total} segments fetched successfully.")
    if errors:
        print(f"  {errors} segments failed (will fall back to straight lines).")
    print(f"  Output: {outpath} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
