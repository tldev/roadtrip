#!/usr/bin/env python3
"""
Re-fetch road geometries for all route proposals.
Uses OSRM (fast, free). Updates data/route-geometries.json proposals section.
"""

import json
import time
import urllib.request

OSRM_BASE = "https://router.project-osrm.org/route/v1/driving"
RATE_LIMIT = 1.0


def fetch_osrm(lat1, lng1, lat2, lng2):
    url = f"{OSRM_BASE}/{lng1},{lat1};{lng2},{lat2}?overview=full&geometries=geojson"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SabbyRoadtrip/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            if data.get("code") != "Ok" or not data.get("routes"):
                return None
            coords = data["routes"][0]["geometry"]["coordinates"]
            return [[c[1], c[0]] for c in coords]
    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def main():
    with open("data/route-proposals.json") as f:
        proposals = json.load(f)
    with open("data/route-geometries.json") as f:
        geometries = json.load(f)

    # Clear old proposal geometries
    geometries["proposals"] = {}

    total = 0
    errors = 0
    segments = sum(1 for r in proposals["routes"] for d in r["days"] if d["driving_hours"] > 0)
    print(f"Fetching {segments} route segments")
    print(f"Estimated time: ~{segments * 1.5:.0f} seconds\n")

    for route in proposals["routes"]:
        print(f"Route {route['id']}: {route['name']}")
        for day in route["days"]:
            if day["driving_hours"] <= 0:
                continue
            total += 1
            key = f"{route['id']}-{day['day']}"
            sc = day["start_coords"]
            ec = day["end_coords"]
            print(f"  [{total}/{segments}] Day {day['day']}: {day['start'][:25]} -> {day['end'][:25]}...", end=" ", flush=True)

            coords = fetch_osrm(sc[0], sc[1], ec[0], ec[1])
            if coords:
                geometries["proposals"][key] = coords
                print(f"OK ({len(coords)} pts)")
            else:
                errors += 1
                print("FAILED")

            if total < segments:
                time.sleep(RATE_LIMIT)

    with open("data/route-geometries.json", "w") as f:
        json.dump(geometries, f)

    print(f"\nDone! {total - errors}/{total} segments fetched.")
    if errors:
        print(f"  {errors} failed (will use straight lines).")


if __name__ == "__main__":
    main()
