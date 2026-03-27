#!/usr/bin/env python3
"""
Fetch drive times between consecutive stops for each route day.
Uses OSRM (free, no API key) to get real driving durations.
Stores results in data/route-proposals.json as drive_time_from_prev on each highlight.

Usage: python3 scripts/fetch-drive-times.py
"""

import json
import time
import urllib.request
import urllib.error

OSRM_BASE = "https://router.project-osrm.org/route/v1/driving"
RATE_LIMIT = 1.0  # seconds between requests


def fetch_drive_time(lat1, lng1, lat2, lng2):
    """Fetch driving time in hours from OSRM. Returns float or None."""
    url = f"{OSRM_BASE}/{lng1},{lat1};{lng2},{lat2}?overview=false"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SabbyRoadtrip/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            if data.get("code") != "Ok" or not data.get("routes"):
                return None
            duration_sec = data["routes"][0]["duration"]
            return round(duration_sec / 3600, 1)  # convert to hours, 1 decimal
    except Exception as e:
        print(f"    ERROR: {e}")
        return None


def main():
    with open("data/route-proposals.json") as f:
        data = json.load(f)

    total = 0
    errors = 0

    # Count total segments
    grand_total = 0
    for route in data["routes"]:
        for day in route["days"]:
            stops = [day["start_coords"]]
            for hl in day["highlights"]:
                if hl.get("coords"):
                    stops.append(hl["coords"])
            stops.append(day["end_coords"])
            grand_total += len(stops) - 1

    print(f"Fetching drive times for {grand_total} segments across {len(data['routes'])} routes")
    print(f"Estimated time: ~{grand_total * 1.5:.0f} seconds\n")

    for route in data["routes"]:
        print(f"Route {route['id']}: {route['name']}")
        for day in route["days"]:
            # Build ordered stop list: start -> highlights -> end
            prev_name = day["start"]
            prev_coords = day["start_coords"]

            for hl in day["highlights"]:
                if not hl.get("coords"):
                    continue
                total += 1
                print(f"  [{total}/{grand_total}] {prev_name[:25]} -> {hl['name'][:25]}...", end=" ", flush=True)

                dt = fetch_drive_time(prev_coords[0], prev_coords[1], hl["coords"][0], hl["coords"][1])
                if dt is not None:
                    hl["drive_time_from_prev"] = dt
                    hl["drive_time_prev_name"] = prev_name.split(",")[0]  # short name
                    print(f"{dt}h")
                else:
                    errors += 1
                    print("FAILED")

                prev_coords = hl["coords"]
                prev_name = hl["name"]

                if total < grand_total:
                    time.sleep(RATE_LIMIT)

            # Last segment: last highlight -> day end
            total += 1
            print(f"  [{total}/{grand_total}] {prev_name[:25]} -> {day['end'][:25]}...", end=" ", flush=True)
            dt = fetch_drive_time(prev_coords[0], prev_coords[1], day["end_coords"][0], day["end_coords"][1])
            if dt is not None:
                # Store on the day itself for reference
                day["drive_time_to_end"] = dt
                day["drive_time_last_stop"] = prev_name.split(",")[0]
                print(f"{dt}h")
            else:
                errors += 1
                print("FAILED")

            if total < grand_total:
                time.sleep(RATE_LIMIT)

    # Save
    with open("data/route-proposals.json", "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    print(f"\nDone! {total - errors}/{total} segments computed.")
    if errors:
        print(f"  {errors} segments failed.")
    print("  Updated data/route-proposals.json")


if __name__ == "__main__":
    main()
