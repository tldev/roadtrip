#!/usr/bin/env python3
"""
Fetch real, location-specific images from Wikimedia Commons for all attractions.
Outputs data/attraction-images.json with direct URLs for each attraction.

Uses the Wikimedia Commons search API (free, no API key).
Rate limited to ~1 request/second.

Usage: python3 scripts/fetch-attraction-images.py
"""

import json
import time
import urllib.request
import urllib.parse
import re

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
PHOTOS_PER_ATTRACTION = 5
RATE_LIMIT = 1.0
DATA_DIR = "data"

# Better search terms for attractions whose names alone don't search well
SEARCH_OVERRIDES = {
    "Roy's Cafe Amboy": "Roy's Motel Cafe Amboy Route 66",
    "Route 66 Museum Kingman": "Route 66 Museum Kingman Arizona",
    "Hualapai Mountain Park": "Hualapai Mountains Arizona",
    "Bell Rock Pathway": "Bell Rock Sedona Arizona",
    "Tlaquepaque Arts Village": "Tlaquepaque Sedona",
    "West Fork Oak Creek Trail": "West Fork Oak Creek Sedona",
    "Airport Mesa Overlook": "Airport Mesa Sedona vortex",
    "Page Springs Cellars": "Page Springs vineyard Cornville Arizona",
    "Standin' on the Corner Park Winslow": "Standin Corner Winslow Arizona",
    "El Rancho Hotel Gallup": "El Rancho Hotel Gallup New Mexico",
    "Bearizona Wildlife Park": "Bearizona Williams Arizona",
    "Route 66 Historic Downtown Williams": "Williams Arizona Route 66 downtown",
    "Mather Point": "Mather Point Grand Canyon",
    "Rim Trail": "Grand Canyon Rim Trail",
    "Desert View Watchtower": "Desert View Watchtower Grand Canyon",
    "Shoshone Point": "Shoshone Point Grand Canyon",
    "Hopi Point Sunset": "Hopi Point Grand Canyon sunset",
    "Grand Canyon Dark Sky Park": "Grand Canyon night sky stars",
    "Cameron Trading Post": "Cameron Trading Post Arizona",
    "Moenkopi Dinosaur Tracks": "Moenkopi dinosaur tracks Arizona",
    "Four Corners Monument": "Four Corners Monument USA",
    "Durango Dog Park": "Durango Colorado town",
    "Animas River Trail": "Animas River Trail Durango",
    "Carver Brewing Company": "Durango Colorado brewery",
    "Smelter Mountain Trail": "Smelter Mountain Durango",
    "Alabama Hills": "Alabama Hills Lone Pine California",
    "Mobius Arch": "Mobius Arch Alabama Hills",
    "Mt. Whitney Portal Road": "Whitney Portal Road Sierra Nevada",
    "Bishop, CA": "Bishop California Eastern Sierra",
    "Tonopah Stargazing Park": "Tonopah Nevada night sky",
    "Mizpah Hotel": "Mizpah Hotel Tonopah Nevada",
    "Tonopah Brewing Company": "Tonopah Nevada town",
    "Pa'rus Trail": "Pa'rus Trail Zion",
    "Scenic Byway 12": "Scenic Byway 12 Utah",
    "Red Canyon": "Red Canyon Utah Dixie National Forest",
    "Goblin Valley State Park": "Goblin Valley State Park Utah",
    "Corona Arch Trail": "Corona Arch Moab Utah",
    "Grandstaff Trail": "Negro Bill Canyon Moab",
    "Moab KOA": "Moab Utah camping",
    "Vail Village": "Vail Village Colorado",
    "Eisenhower Tunnel": "Eisenhower Tunnel Colorado I-70",
    "Hearst Castle Vista Point": "Hearst Castle San Simeon",
    "Morro Rock & Morro Bay": "Morro Rock Morro Bay California",
    "Santa Barbara Waterfront": "Santa Barbara waterfront Stearns Wharf",
    "Route 66 Dog Park Kingman": "Kingman Arizona Route 66",
    "Arizona Route 66 Museum": "Route 66 Museum Kingman Arizona",
    "Mount Lemmon Scenic Drive": "Mount Lemmon Tucson scenic drive",
    "Catalina State Park": "Catalina State Park Tucson Arizona",
    "US-82 Cloudcroft Highway": "US 82 Cloudcroft New Mexico mountain road",
    "Osha Trail": "Cloudcroft New Mexico hiking",
    "Dog Canyon Trail": "Dog Canyon Sacramento Mountains",
    "Rim Trail Cloudcroft": "Cloudcroft New Mexico rim trail",
    "16 Springs Canyon Campground": "Lincoln National Forest camping",
    "National Solar Observatory at Sunspot": "National Solar Observatory Sunspot New Mexico",
    "Rio Grande Bosque Trail": "Rio Grande Bosque Albuquerque",
    "Old Town Albuquerque": "Old Town Albuquerque New Mexico",
    "Santa Fe Plaza": "Santa Fe Plaza New Mexico",
    "Las Vegas, NM": "Las Vegas New Mexico historic plaza",
    "Raton Pass": "Raton Pass Colorado New Mexico",
    "Donner Memorial State Park": "Donner Memorial State Park",
    "Truckee, CA (en route)": "Truckee California downtown",
    "Virginia Lake Park & Off-Leash Dog Park": "Virginia Lake Reno Nevada",
    "Reno Riverwalk District": "Reno Riverwalk District Nevada",
    "Perrine Bridge & Snake River Canyon": "Perrine Bridge Twin Falls Idaho",
    "Centennial Waterfront Park": "Twin Falls Idaho waterfront",
    "Dierkes Lake": "Dierkes Lake Twin Falls",
    "Craters of the Moon National Monument (optional detour)": "Craters of the Moon Idaho",
    "Idaho Falls River Walk": "Idaho Falls River Walk",
    "Freeman Park Off-Leash Dog Area": "Idaho Falls Freeman Park",
    "Tautphaus Park": "Tautphaus Park Idaho Falls",
    "Upper Mesa Falls (en route)": "Upper Mesa Falls Idaho",
    "Rendezvous Ski Trails (Summer Hiking)": "Rendezvous Trails West Yellowstone summer",
    "Grizzly & Wolf Discovery Center": "Grizzly Wolf Discovery Center West Yellowstone",
    "Hebgen Lake": "Hebgen Lake Montana",
    "Old Faithful & Upper Geyser Basin": "Old Faithful Yellowstone geyser",
    "Grand Prismatic Spring (roadside view)": "Grand Prismatic Spring Yellowstone",
    "Madison River Valley Wildlife Drive": "Madison River Yellowstone wildlife",
    "Coffin Lake Trails": "West Yellowstone hiking trails",
    "Baker's Hole Campground": "Baker's Hole Campground West Yellowstone",
    "Grand Canyon of the Yellowstone (Artist Point)": "Grand Canyon Yellowstone Artist Point",
    "Hayden Valley Wildlife Viewing": "Hayden Valley Yellowstone bison",
    "Wapiti Valley -- Buffalo Bill Scenic Byway": "Wapiti Valley Buffalo Bill Scenic Byway",
    "Buffalo Bill Center of the West": "Buffalo Bill Center West Cody Wyoming",
    "Shell Falls": "Shell Falls Bighorn Mountains Wyoming",
    "Bighorn Scenic Byway (US-14 over Big Horns)": "Bighorn Scenic Byway US 14 Wyoming",
    "Tongue River Canyon Trail": "Tongue River Canyon Dayton Wyoming",
    "Sheridan Historic Main Street": "Sheridan Wyoming Main Street",
    "Hole in the Wall Country (near Kaycee, WY)": "Hole in the Wall Wyoming Outlaw",
    "Morad Park Off-Leash Dog Area (Casper)": "Casper Wyoming North Platte River",
    "Ayres Natural Bridge Park": "Ayres Natural Bridge Wyoming",
    "Casper, WY (lunch stop)": "Casper Wyoming downtown",
    "Trona Pinnacles": "Trona Pinnacles California",
    "Death Valley - Zabriskie Point": "Zabriskie Point Death Valley",
    "Death Valley - Badwater Basin": "Badwater Basin Death Valley",
    "Wildrose Charcoal Kilns": "Wildrose Charcoal Kilns Death Valley",
    "Navajo Bridge": "Navajo Bridge Marble Canyon Arizona",
    "Wahweap Campground": "Wahweap Lake Powell",
    "Glen Canyon Dam": "Glen Canyon Dam Page Arizona",
    "Durango Animas River Trail": "Animas River Durango Colorado",
    "Smelter Mountain Off-Leash": "Smelter Mountain Durango",
    "Wolf Creek Pass": "Wolf Creek Pass Colorado",
    "San Luis Valley": "San Luis Valley Colorado",
    "Great Sand Dunes (distant view)": "Great Sand Dunes National Park Colorado",
    "Fairplay / South Park": "Fairplay Colorado South Park",
    "Sacramento": "Sacramento California Old Town",
    "Lake Siskiyou": "Lake Siskiyou Mount Shasta California",
    "Mount Shasta Headwaters": "Mount Shasta City Park headwaters",
    "Pilot Butte": "Pilot Butte Bend Oregon",
    "Deschutes River Trail": "Deschutes River Trail Bend Oregon",
    "Tumalo Falls": "Tumalo Falls Bend Oregon",
    "Crux Fermentation Project": "Bend Oregon brewery",
    "Tumalo State Park Campground": "Tumalo State Park Oregon",
    "Worthy Brewing Observatory": "Worthy Brewing Bend Oregon",
    "Shevlin Park": "Shevlin Park Bend Oregon",
    "John Day Fossil Beds - Sheep Rock Unit": "John Day Fossil Beds Sheep Rock Oregon",
    "Kam Wah Chung State Heritage Site": "Kam Wah Chung John Day Oregon",
    "Blue Mountain Scenic Byway": "Blue Mountains Oregon scenic",
    "Boise River Greenbelt": "Boise River Greenbelt Idaho",
    "Freak Alley Gallery": "Freak Alley Gallery Boise Idaho",
    "Hemingway Memorial": "Hemingway Memorial Ketchum Idaho Sun Valley",
    "Draper Preserve": "Draper Preserve Hailey Idaho",
    "Galena Summit Overlook": "Galena Summit Idaho Sawtooth",
    "Sawtooth Brewery": "Stanley Idaho Sawtooth Mountains",
    "Grand Teton NP - Mormon Row": "Mormon Row Grand Teton barn",
    "Cache Creek Trail System": "Cache Creek Trail Jackson Wyoming",
    "Togwotee Pass": "Togwotee Pass Wyoming Absaroka",
    "Dubois, WY": "Dubois Wyoming Wind River",
    "Elk Mountain & Medicine Bow": "Elk Mountain Medicine Bow Wyoming",
    "Cheyenne": "Cheyenne Wyoming State Capitol",
    "Pinnacles National Park (West Entrance)": "Pinnacles National Park California",
    "Sequoia Gateway": "Three Rivers California Sequoia Gateway",
    "Mobius Arch Trail": "Mobius Arch Alabama Hills",
    "Movie Road": "Movie Road Alabama Hills",
    "Whitney Portal Road": "Whitney Portal Road Sierra Nevada",
    "Manzanar National Historic Site": "Manzanar National Historic Site",
    "Erick Schat's Bakkery Bishop": "Bishop California Eastern Sierra",
    "Wild Willy's Hot Spring": "Wild Willy Hot Spring Mammoth Lakes",
    "Convict Lake": "Convict Lake California",
    "Mammoth Mountain Scenic Gondola": "Mammoth Mountain California gondola",
    "Horseshoe Lake Dog Beach": "Horseshoe Lake Mammoth Lakes",
    "June Lake Loop": "June Lake Loop California Eastern Sierra",
    "Twin Lakes Campground": "Twin Lakes Bridgeport California",
    "Lakes Basin Drive": "Lakes Basin Eastern Sierra",
    "Mono Lake South Tufa": "Mono Lake South Tufa California",
    "Tonopah Stargazing": "Tonopah Nevada night sky",
    "Nevada Northern Railway": "Nevada Northern Railway Ely",
    "Cave Lake State Park": "Cave Lake State Park Ely Nevada",
    "Ward Charcoal Ovens": "Ward Charcoal Ovens State Historic Park",
    "Great Basin NP (distant view)": "Great Basin National Park Nevada",
    "San Rafael Swell": "San Rafael Swell Utah",
    "Glenwood Canyon": "Glenwood Canyon Colorado I-70",
    "Glenwood Springs": "Glenwood Springs Colorado",
    "San Luis Obispo Downtown": "San Luis Obispo California downtown",
    "Morro Rock": "Morro Rock California",
    "Route 66 Mother Road Museum": "Route 66 Mother Road Museum Barstow",
    "Calico Ghost Town": "Calico Ghost Town California",
    "Snow Cap Drive-In Seligman": "Snow Cap Drive-In Seligman Arizona",
    "Route 66 Seligman": "Seligman Arizona Route 66",
    "Flagstaff Historic Downtown": "Flagstaff Arizona historic downtown Route 66",
    "Sunset Crater Lava Flow Trail": "Sunset Crater Volcano National Monument",
    "Bonito Campground": "Bonito Campground Flagstaff",
    "Walnut Canyon National Monument": "Walnut Canyon National Monument Flagstaff",
    "Fatman's Loop Trail": "Fatman's Loop Trail Flagstaff",
    "Lake Mary": "Lake Mary Flagstaff Arizona",
    "Meteor Crater": "Meteor Crater Arizona Winslow",
    "Route 66 Neon Arch Grants": "Route 66 Grants New Mexico",
    "Canyon Road Santa Fe": "Canyon Road Santa Fe galleries",
    "Frank Ortiz Dog Park": "Santa Fe New Mexico park",
    "Spanish Peaks": "Spanish Peaks Colorado",
    "Cherry Creek State Park": "Cherry Creek State Park Denver",
    "Palmer Park": "Palmer Park Colorado Springs",
    "Bidwell Park -- Upper Park": "Bidwell Park Upper Park Chico California",
    "Bidwell Park -- Lower Park & One-Mile Recreation Area": "Bidwell Park Lower Park Chico",
    "Sierra Nevada Brewing Company": "Sierra Nevada Brewing Chico California",
    "Downtown Chico": "Chico California downtown",
    "Feather River Canyon (en route)": "Feather River Canyon California",
    "Winnemucca Sand Dunes": "Winnemucca Sand Dunes Nevada",
    "Martin Hotel -- Basque Dining": "Martin Hotel Winnemucca Nevada Basque",
    "Humboldt River Walk": "Winnemucca Nevada Humboldt River",
    "Shoshone Falls (en route, Twin Falls)": "Shoshone Falls Twin Falls Idaho",
    "Camel's Back Park & Ridge to Rivers Trails": "Camels Back Park Boise Idaho",
    "Traveler's Rest State Park": "Travelers Rest State Park Montana",
    "Rattlesnake National Recreation Area": "Rattlesnake Wilderness Missoula Montana",
    "Mount Sentinel 'M' Trail": "Mount Sentinel M Trail Missoula",
    "Carousel for Missoula & Caras Park": "Carousel Missoula Montana Caras Park",
    "Gates of the Mountains Viewpoint (en route, near Helena)": "Gates of the Mountains Montana",
    "Hyalite Canyon Recreation Area": "Hyalite Canyon Bozeman Montana",
    "Peets Hill / Burke Park": "Peet's Hill Bozeman Montana",
    "Downtown Bozeman Main Street": "Bozeman Montana Main Street downtown",
    "Palisade Falls": "Palisade Falls Bozeman Montana Hyalite",
    "Grotto Falls": "Grotto Falls Hyalite Canyon Montana",
    "Hyalite Reservoir": "Hyalite Reservoir Bozeman Montana",
    "Beehive Basin Trail (Big Sky detour)": "Beehive Basin Trail Big Sky Montana",
    "Little Bighorn Battlefield National Monument (en route)": "Little Bighorn Battlefield Montana",
    "Bighorn Scenic Byway (US-14)": "Bighorn Scenic Byway US 14 Wyoming",
    "Historic Downtown Sheridan & The Mint Bar": "Sheridan Wyoming Mint Bar",
    "Tongue River Trail & Kendrick Park": "Tongue River Sheridan Wyoming",
    "Buffalo, WY -- Clear Creek Trail": "Buffalo Wyoming Clear Creek Trail",
    "National Historic Trails Interpretive Center (Casper)": "National Historic Trails Center Casper Wyoming",
    "Cheyenne, WY -- State Capitol": "Cheyenne Wyoming State Capitol",
}


def search_commons(query, limit=PHOTOS_PER_ATTRACTION + 3):
    """Search Wikimedia Commons for images. Returns list of direct URLs."""
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
            # Only want photos (not SVGs, icons, maps, etc.)
            if "image" not in mime or "svg" in mime:
                continue
            # Skip tiny images
            if width < 400 or height < 300:
                continue
            thumb = info.get("thumburl") or info.get("url")
            if thumb:
                urls.append(thumb)
        return urls[:PHOTOS_PER_ATTRACTION]
    except Exception as e:
        print(f"    API error: {e}")
        return []


def main():
    with open(f"{DATA_DIR}/route-proposals.json") as f:
        data = json.load(f)

    # Collect unique attractions
    attractions = {}  # name -> {type, description, coords}
    for route in data["routes"]:
        for day in route["days"]:
            for hl in day.get("highlights", []):
                if hl["name"] not in attractions:
                    attractions[hl["name"]] = {
                        "type": hl["type"],
                        "description": hl["description"],
                        "coords": hl.get("coords"),
                    }

    print(f"Found {len(attractions)} unique attractions")
    print(f"Fetching {PHOTOS_PER_ATTRACTION} images each from Wikimedia Commons")
    print(f"Estimated time: ~{len(attractions) * RATE_LIMIT:.0f} seconds\n")

    results = {}
    total = len(attractions)
    success = 0
    partial = 0
    failed = 0

    for i, (name, info) in enumerate(attractions.items(), 1):
        search_term = SEARCH_OVERRIDES.get(name, name)
        print(f"[{i}/{total}] {name}", end="", flush=True)
        if search_term != name:
            print(f" (searching: {search_term[:50]})", end="", flush=True)

        urls = search_commons(search_term)

        if len(urls) >= 3:
            status = "OK"
            success += 1
        elif len(urls) > 0:
            status = "PARTIAL"
            partial += 1
        else:
            status = "FAILED"
            failed += 1

        results[name] = {
            "photos": urls,
            "type": info["type"],
        }
        print(f" — {status} ({len(urls)} photos)")

        if i < total:
            time.sleep(RATE_LIMIT)

    # Save results
    outpath = f"{DATA_DIR}/attraction-images.json"
    with open(outpath, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nDone!")
    print(f"  Success (3+ photos): {success}")
    print(f"  Partial (1-2 photos): {partial}")
    print(f"  Failed (0 photos): {failed}")
    print(f"  Output: {outpath}")


if __name__ == "__main__":
    main()
