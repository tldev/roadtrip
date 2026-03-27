#!/usr/bin/env python3
"""
Fetch real road geometries AND drive times for all route proposals using Valhalla.
Updates both route-geometries.json (proposals section) and route-proposals.json.
"""

import json
import time
import urllib.request
import urllib.parse

VALHALLA_BASE = "https://valhalla1.openstreetmap.de/route"
RATE_LIMIT = 1.2  # seconds between requests


def decode_polyline(encoded, precision=6):
    inv = 10**-precision
    decoded = []
    lat = lng = 0
    i = 0
    while i < len(encoded):
        shift = result = 0
        while True:
            b = ord(encoded[i]) - 63
            i += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        lat += (~(result >> 1) if result & 1 else result >> 1)
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
    """Returns (geometry_points, duration_hours) or (None, None)."""
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
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode())
            trip = data.get("trip", {})
            legs = trip.get("legs", [{}])
            shape = legs[0].get("shape", "")
            duration = trip.get("summary", {}).get("time", 0)
            if not shape:
                return None, None
            points = decode_polyline(shape, precision=6)
            hours = round(duration / 3600, 1)
            return points, hours
    except Exception as e:
        print(f"  ERROR: {e}")
        return None, None


def main():
    with open("data/route-proposals.json") as f:
        proposals = json.load(f)
    with open("data/route-geometries.json") as f:
        geometries = json.load(f)

    # Clear stale proposal geometries
    geometries["proposals"] = {}

    # Phase 1: Fetch day-level geometries (start -> end for each driving day)
    driving_days = [(r, d) for r in proposals["routes"] for d in r["days"] if d["driving_hours"] > 0]
    print(f"Phase 1: Fetching {len(driving_days)} day-level road geometries via Valhalla\n")

    geo_ok = 0
    for i, (route, day) in enumerate(driving_days):
        key = f"{route['id']}-{day['day']}"
        sc, ec = day["start_coords"], day["end_coords"]
        print(f"  [{i+1}/{len(driving_days)}] Route {route['id']} Day {day['day']}: "
              f"{day['start'][:25]} -> {day['end'][:25]}...", end=" ", flush=True)

        pts, _ = fetch_valhalla(sc[0], sc[1], ec[0], ec[1])
        if pts:
            geometries["proposals"][key] = pts
            geo_ok += 1
            print(f"OK ({len(pts)} pts)")
        else:
            print("FAILED")

        if i < len(driving_days) - 1:
            time.sleep(RATE_LIMIT)

    # Save geometries
    with open("data/route-geometries.json", "w") as f:
        json.dump(geometries, f)
    print(f"\nPhase 1 done: {geo_ok}/{len(driving_days)} geometries fetched.\n")

    # Phase 2: Fetch drive times between consecutive stops within each day
    segments = []
    for route in proposals["routes"]:
        for day in route["days"]:
            prev_name = day["start"]
            prev_coords = day["start_coords"]
            for hl in day["highlights"]:
                if not hl.get("coords"):
                    continue
                segments.append((route, day, hl, prev_name, prev_coords))
                prev_coords = hl["coords"]
                prev_name = hl["name"]

    print(f"Phase 2: Fetching {len(segments)} stop-to-stop drive times via Valhalla\n")

    dt_ok = 0
    for i, (route, day, hl, prev_name, prev_coords) in enumerate(segments):
        print(f"  [{i+1}/{len(segments)}] {prev_name[:25]} -> {hl['name'][:25]}...", end=" ", flush=True)

        _, hours = fetch_valhalla(prev_coords[0], prev_coords[1], hl["coords"][0], hl["coords"][1])
        if hours is not None:
            hl["drive_time_from_prev"] = hours
            hl["drive_time_prev_name"] = prev_name.split(",")[0]
            dt_ok += 1
            print(f"{hours}h")
        else:
            print("FAILED")

        if i < len(segments) - 1:
            time.sleep(RATE_LIMIT)

    # Save proposals with drive times
    with open("data/route-proposals.json", "w") as f:
        json.dump(proposals, f, indent=2)
        f.write("\n")

    print(f"\nPhase 2 done: {dt_ok}/{len(segments)} drive times computed.")
    print("Updated data/route-geometries.json and data/route-proposals.json")


if __name__ == "__main__":
    main()
