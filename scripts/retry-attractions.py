#!/usr/bin/env python3
"""Retry fetching images for attractions that failed or got < 3 photos."""

import json
import time
import urllib.request
import urllib.parse

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
DATA_DIR = "data"

RETRY_SEARCHES = {
    # 0 photos - need completely different searches
    "Flagstaff Urban Trail System": ["Flagstaff Arizona ponderosa pine trail", "Flagstaff Arizona forest path", "Flagstaff Arizona urban hiking"],
    "Mother Road Brewing Company": ["Mother Road Brewing Flagstaff", "Flagstaff Arizona brewery beer", "Route 66 Flagstaff beer"],
    "Kanab Creek Walk": ["Kanab Utah Main Street", "Kanab Utah town", "Kanab Creek Utah"],
    "Bryce Canyon Shared Use Path": ["Bryce Canyon road ponderosa", "Bryce Canyon paved trail", "Bryce Canyon Utah forest"],
    "San Rafael Swell Viewpoint": ["San Rafael Swell Utah", "San Rafael Reef Utah", "Black Dragon Canyon Utah"],
    "Colorado River Scenic Byway": ["Glenwood Canyon Colorado River", "Glenwood Canyon I-70 Colorado", "Colorado River Glenwood"],
    "Ely Renaissance Village": ["Ely Nevada historic", "Ely Nevada town history", "White Pine County Nevada"],
    "San Rafael Swell - I-70": ["San Rafael Swell", "San Rafael Reef", "I-70 Utah San Rafael"],
    "Wahweap Overlook Trail": ["Wahweap Marina Lake Powell", "Lake Powell Page Arizona", "Lake Powell overlook"],
    # 1 photo - add more
    "Greenway Trail": ["Flagstaff Arizona trail ponderosa", "Rio de Flag Flagstaff", "Wheeler Park Flagstaff"],
    "Seven Magic Mountains": ["Seven Magic Mountains", "Ugo Rondinone desert boulders", "Seven Magic Mountains Nevada art"],
    "Santa Fe Plaza Morning Walk": ["Santa Fe Plaza adobe", "Santa Fe New Mexico plaza cathedral", "Palace of Governors Santa Fe"],
    "Animas River Trail Durango": ["Durango Colorado Animas River", "Durango Colorado downtown river", "Animas River Colorado"],
    "Vail Pass Summit": ["Vail Pass Colorado mountains", "Vail Pass I-70 mountain", "Vail Colorado summit mountains"],
    # 2 photos - need 1+ more
    "Red Canyon Trails": ["Red Canyon Dixie National Forest", "Red Canyon Highway 12 Utah", "Red Canyon hoodoos Utah"],
    "Springdale Town Walk": ["Springdale Zion Utah town", "Springdale Utah", "Zion gateway town Springdale"],
    "Cave Lake Trails": ["Cave Lake Nevada", "Schell Creek Range Nevada", "Cave Lake State Park"],
    "Ely Main Street Walk": ["Ely Nevada Hotel Nevada", "Ely Nevada Aultman Street", "Hotel Nevada Ely"],
}


def search_commons(query, limit=8):
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": query,
        "gsrlimit": str(limit),
        "gsrnamespace": "6",
        "prop": "imageinfo",
        "iiprop": "url|mime|size",
        "iiurlwidth": "1200",
        "format": "json",
    }
    url = f"{COMMONS_API}?{urllib.parse.urlencode(params)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SabbyRoadtrip/1.0 (personal travel planner)"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        pages = data.get("query", {}).get("pages", {})
        urls = []
        for page in sorted(pages.values(), key=lambda x: x.get("index", 999)):
            info = page.get("imageinfo", [{}])[0]
            mime = info.get("mime", "")
            width = info.get("width", 0)
            height = info.get("height", 0)
            thumb_url = info.get("thumburl") or info.get("url", "")
            if "image" not in mime or "svg" in mime:
                continue
            if width < 400 or height < 300:
                continue
            if ".tif" in thumb_url.lower():
                continue
            if thumb_url:
                urls.append(thumb_url)
        return urls
    except Exception as e:
        print(f"    API error: {e}")
        return []


def main():
    with open(f"{DATA_DIR}/attraction-data.json") as f:
        data = json.load(f)

    total_searches = sum(len(v) for v in RETRY_SEARCHES.values())
    print(f"Retrying {len(RETRY_SEARCHES)} attractions with {total_searches} alternate searches\n")

    search_num = 0
    improved = 0

    for name, searches in RETRY_SEARCHES.items():
        current_photos = data[name]["photos"]
        need = 5 - len(current_photos)
        existing_urls = set(current_photos)

        print(f"{name} ({len(current_photos)} photos, need {need} more)")

        new_urls = []
        for query in searches:
            search_num += 1
            print(f"  Trying: {query}...", end=" ", flush=True)
            results = search_commons(query)
            added = 0
            for url in results:
                if url not in existing_urls and len(new_urls) + len(current_photos) < 5:
                    new_urls.append(url)
                    existing_urls.add(url)
                    added += 1
            print(f"+{added} new")
            time.sleep(1.0)

            if len(new_urls) + len(current_photos) >= 5:
                break

        if new_urls:
            data[name]["photos"] = current_photos + new_urls
            print(f"  → Now has {len(data[name]['photos'])} photos\n")
            improved += 1
        else:
            print(f"  → Still at {len(current_photos)} photos\n")

    # Save
    with open(f"{DATA_DIR}/attraction-data.json", "w") as f:
        json.dump(data, f, indent=2)

    print(f"Done! Improved {improved}/{len(RETRY_SEARCHES)} attractions")

    # Final report
    still_low = [(n, len(data[n]["photos"])) for n in RETRY_SEARCHES if len(data[n]["photos"]) < 3]
    if still_low:
        print(f"\nStill under 3 photos:")
        for n, c in still_low:
            print(f"  {c}: {n}")


if __name__ == "__main__":
    main()
