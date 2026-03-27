#!/usr/bin/env python3
"""
Fetch images and add descriptions for attractions in the revised route proposals
that are not yet in attraction-data.json.

Merges results into the existing attraction-data.json file.
"""

import json
import time
import urllib.request
import urllib.parse

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
PHOTOS_PER_ATTRACTION = 5
RATE_LIMIT = 1.0
DATA_DIR = "data"

# Search overrides for new attractions
SEARCH_OVERRIDES = {
    "Animas River Trail Durango": "Animas River Durango Colorado trail",
    "Best Friends Animal Sanctuary Visit": "Best Friends Animal Sanctuary Kanab Utah",
    "Bryce Canyon Rim Trail": "Bryce Canyon National Park rim trail",
    "Bryce Canyon Shared Use Path": "Bryce Canyon National Park pathway",
    "Capitol Reef Petroglyphs": "Capitol Reef National Park petroglyphs",
    "Capitol Reef Scenic Drive": "Capitol Reef National Park scenic drive",
    "Cave Lake Shoreline Trail": "Cave Lake State Park Ely Nevada",
    "Cave Lake Trails": "Cave Lake State Park Nevada hiking",
    "Chains Trail Area": "Capitol Reef Waterpocket Fold",
    "Colorado National Monument": "Colorado National Monument Grand Junction",
    "Colorado River Scenic Byway": "Colorado River scenic byway Glenwood Springs",
    "Coral Pink Sand Dunes State Park": "Coral Pink Sand Dunes State Park Utah",
    "Eisenhower Tunnel Vista": "Eisenhower Tunnel Colorado Interstate 70",
    "Ely Main Street Walk": "Ely Nevada downtown Main Street",
    "Ely Renaissance Village": "Ely Nevada Renaissance Village",
    "Flagstaff Urban Trail System": "Flagstaff Urban Trail Arizona hiking",
    "Fremont River Trail": "Fremont River Trail Capitol Reef",
    "Glen Canyon Dam Overlook": "Glen Canyon Dam Page Arizona overlook",
    "Glenwood Canyon Rest Stop": "Glenwood Canyon Colorado I-70 rest area",
    "Grafton Ghost Town": "Grafton Ghost Town Zion Utah",
    "Grand Canyon Rim Trail": "Grand Canyon South Rim Trail",
    "Great Basin Highway Overlook": "Great Basin Highway Nevada US 93",
    "Great Basin Highway Views": "Great Basin Highway Nevada landscape",
    "Great Sand Dunes View": "Great Sand Dunes National Park Colorado",
    "Greenway Trail": "Flagstaff Urban Trail System Arizona",
    "Kanab Creek Walk": "Kanab Creek Utah town walk",
    "Mojave National Preserve": "Mojave National Preserve California",
    "Mojave National Preserve - Cima Road": "Mojave National Preserve Cima Road Joshua trees",
    "Moqui Cave": "Moqui Cave Kanab Utah",
    "Morro Rock Vista": "Morro Rock Morro Bay California",
    "Mother Road Brewing Company": "Flagstaff Arizona craft brewery",
    "Panorama Point": "Panorama Point Capitol Reef Utah",
    "Red Canyon Trails": "Red Canyon Utah Dixie National Forest hiking",
    "Red Rock Canyon": "Red Rock Canyon National Conservation Area Nevada",
    "Sacramento Old Town": "Sacramento Old Town California historic",
    "San Rafael Swell - I-70": "San Rafael Swell Utah I-70 corridor",
    "San Rafael Swell - I-70 Corridor": "San Rafael Swell Utah Interstate 70",
    "San Rafael Swell Viewpoint": "San Rafael Swell Utah scenic viewpoint",
    "Sand Mountain Recreation Area": "Sand Mountain Nevada recreation area",
    "Santa Fe Plaza Morning Walk": "Santa Fe Plaza New Mexico morning",
    "Seven Magic Mountains": "Seven Magic Mountains Las Vegas art",
    "Springdale Town Walk": "Springdale Utah Zion gateway town",
    "Tehachapi Wind Farm": "Tehachapi Pass wind farm California turbines",
    "Tonopah Historic Mining Park": "Tonopah Historic Mining Park Nevada",
    "Vail Pass Summit": "Vail Pass Colorado summit I-70",
    "Valley of Fire State Park": "Valley of Fire State Park Nevada",
    "Wahweap Overlook Trail": "Wahweap overlook Lake Powell Arizona",
    "Zion Canyon Scenic Drive": "Zion Canyon scenic drive Utah",
}

# Descriptions for all 48 new attractions
DESCRIPTIONS = {
    "Animas River Trail Durango": [
        "Paved riverwalk trail winding through downtown Durango along the scenic Animas River — perfect for dogs on leash",
        "Connects to parks, bridges, and outdoor seating areas with mountain views in every direction",
        "The river corridor attracts ducks, herons, and the occasional kayaker; great people-watching from the path",
        "Easy 7-mile trail that passes through the heart of Durango's historic district and brewery row",
    ],
    "Best Friends Animal Sanctuary Visit": [
        "The nation's largest no-kill animal sanctuary, set in Angel Canyon near Kanab with 3,700 acres of red-rock landscape",
        "Free guided tours let you meet the animals — dogs, cats, horses, parrots, pigs, and more awaiting adoption",
        "Dogs are welcome on the tour; the sanctuary's mission has saved hundreds of thousands of animals since 1984",
        "Gift shop and café on site; the canyon setting alone is worth the drive from Kanab",
    ],
    "Bryce Canyon Rim Trail": [
        "Paved trail along the rim of Bryce Amphitheater with nonstop views of thousands of orange-red hoodoo formations",
        "Dogs allowed on the Rim Trail — one of the few trails in the park open to pets — with easy access from parking areas",
        "Connects Sunrise, Sunset, Inspiration, and Bryce Points over 5.5 miles of mostly flat walking",
        "Elevation sits above 8,000 feet, keeping temperatures comfortable even in summer heat",
    ],
    "Bryce Canyon Shared Use Path": [
        "3.6-mile paved multi-use path between the park entrance and Inspiration Point — ideal for dogs and bikes",
        "Runs parallel to the main park road through ponderosa pine forest with glimpses of red rock through the trees",
        "Avoids the crowded shuttle system while still connecting key viewpoints along the canyon rim",
        "Gentle grades and wide pavement make this an easy walk with dogs; connects to the Rim Trail at multiple points",
    ],
    "Capitol Reef Petroglyphs": [
        "Ancient Fremont culture petroglyphs pecked into dark desert-varnished rock along Highway 24 in Capitol Reef",
        "A boardwalk viewpoint makes the rock art easy to see — human figures, bighorn sheep, and abstract designs dating back 1,000+ years",
        "Free roadside stop with no entrance fee required; the petroglyphs are visible without any hiking",
        "Part of a larger concentration of Fremont rock art throughout the Waterpocket Fold region",
    ],
    "Capitol Reef Scenic Drive": [
        "8-mile paved road cutting south from the Fruita historic district into the heart of the Waterpocket Fold",
        "Towering sandstone walls in every shade of red, orange, and cream frame the drive on both sides",
        "Pulloffs at Capitol Gorge and Grand Wash lead to short canyon walks between 800-foot walls",
        "One of the least-crowded scenic drives in Utah's national parks — often feels like you have the canyon to yourself",
    ],
    "Cave Lake Shoreline Trail": [
        "Easy loop trail around Cave Lake in the Schell Creek Range above Ely, Nevada at 7,300 feet elevation",
        "Piñon-juniper forest and limestone cliffs surround the small reservoir — a cool mountain oasis in the Great Basin",
        "Dog-friendly trail with lake access for swimming; fall brings golden aspens along the shoreline",
        "Quiet campground adjacent with first-come sites — one of Nevada's hidden gems away from any crowds",
    ],
    "Cave Lake Trails": [
        "Network of trails through the Schell Creek Range around Cave Lake — from easy lakeside walks to ridge hikes",
        "Piñon-juniper woodland gives way to mountain mahogany at higher elevations with views across the Great Basin",
        "Dog-friendly trails with a mix of terrain; the lake itself allows wading for hot dogs",
        "At 7,300 feet, the air is cool and dry even when the valleys below bake in summer heat",
    ],
    "Chains Trail Area": [
        "Rugged backcountry area in Capitol Reef where the Waterpocket Fold creates dramatic tilted rock layers",
        "Named for the chains once bolted into the slickrock to help wagons descend — now a popular hiking area",
        "Views from the top of the fold span the entire desert basin below in a sweeping panorama",
        "One of the most remote and least-visited areas of Capitol Reef, offering genuine solitude",
    ],
    "Colorado National Monument": [
        "2,000-foot-deep red-rock canyons carved into the Colorado Plateau just outside Grand Junction",
        "Rim Rock Drive winds 23 miles along the canyon edge with dramatic overlooks at every pulloff",
        "Monoliths like Independence Monument and Coke Ovens rise from the canyon floor in shades of crimson and ochre",
        "Dog-friendly on the rim road and overlook areas; cooler mornings bring bighorn sheep sightings near the road",
    ],
    "Colorado River Scenic Byway": [
        "Scenic stretch along the Colorado River between Glenwood Springs and Grand Junction on I-70",
        "The river carves through Glenwood Canyon with 1,800-foot walls — one of the most dramatic interstate drives in America",
        "Rest areas and bike path access let you stop and walk along the river at several points",
        "Bald eagles, great blue herons, and rafters share the river corridor in the narrow canyon",
    ],
    "Coral Pink Sand Dunes State Park": [
        "Bright coral-pink sand dunes rising up to 2,000 feet between red Navajo sandstone cliffs near Kanab, Utah",
        "Dogs are welcome on leash throughout the park — the soft sand is easy on paws and fun to explore",
        "The unique pink color comes from eroding Navajo sandstone; wind funneling through the notch between the Moquith and Moccasin mountains builds the dunes",
        "Less crowded than the big national parks, with a peaceful campground tucked against the dune field",
    ],
    "Eisenhower Tunnel Vista": [
        "Highway pull-off near the Eisenhower-Johnson Memorial Tunnel — the highest point on the Interstate Highway System at 11,158 feet",
        "Views of the Continental Divide and surrounding peaks of the Arapaho National Forest",
        "The tunnel itself bores 1.7 miles through the divide; a quick stop to stretch legs at altitude before descending toward Denver",
        "Winter snowpack can linger into June at this elevation — a dramatic alpine landscape visible right from the highway",
    ],
    "Ely Main Street Walk": [
        "Historic downtown Ely with murals, antique shops, and a preserved small-town Nevada atmosphere along Aultman Street",
        "The Hotel Nevada anchors the strip — a 1929 landmark that was once the tallest building in the state",
        "Dog-friendly sidewalks past the old railroad depot, courthouses, and local cafés that feel like stepping back in time",
        "Ely serves as the gateway to Great Basin National Park, but the town itself has genuine frontier character",
    ],
    "Ely Renaissance Village": [
        "Open-air heritage village showcasing the multicultural history of White Pine County through restored cabins and cottages",
        "Buildings represent the Chinese, Greek, Basque, Italian, and other immigrant communities that built the mining town",
        "A free, self-guided walking tour through the small village adjacent to downtown Ely",
        "Gives context to how diverse the mining communities of rural Nevada actually were in the 19th and early 20th centuries",
    ],
    "Flagstaff Urban Trail System": [
        "Extensive network of paved and natural-surface trails through ponderosa pine forests within Flagstaff city limits",
        "FUTS connects neighborhoods, parks, and downtown to the surrounding national forest — over 56 miles of trails",
        "Dog-friendly and well-marked; the trails see joggers, cyclists, and dog walkers year-round at 7,000 feet elevation",
        "A rare chance to walk through old-growth ponderosa pine forest without leaving town",
    ],
    "Fremont River Trail": [
        "Easy 1.5-mile round-trip trail along the Fremont River through the Fruita historic district in Capitol Reef",
        "Follows the cottonwood-lined river past the pioneer orchards where you can pick fruit in season (cherries, apples, peaches)",
        "Dogs allowed on leash; the shaded riverside path stays cool even on hot Utah afternoons",
        "Deer and wild turkeys are common along the river; the Fruita schoolhouse is a short side trip",
    ],
    "Glen Canyon Dam Overlook": [
        "Viewpoint overlooking the 710-foot concrete arch dam that created Lake Powell, visible from Highway 89 in Page, Arizona",
        "The Carl Hayden Visitor Center offers exhibits on the dam's construction and the Colorado River system",
        "Dramatic perspective looking down into the narrow Glen Canyon with turquoise water below",
        "Free viewpoint accessible from the highway; the dam and bridge make for impressive photography at any time of day",
    ],
    "Glenwood Canyon Rest Stop": [
        "Scenic rest area carved into the narrow canyon along I-70, surrounded by 1,800-foot limestone and granite walls",
        "Adjacent to the Glenwood Canyon Recreation Path — a paved bike and walking trail along the Colorado River",
        "One of the most dramatic rest stop settings in the country; great for letting dogs stretch their legs",
        "Engineered to blend with the canyon walls, the highway and rest area are an engineering marvel in their own right",
    ],
    "Grafton Ghost Town": [
        "Photogenic abandoned Mormon settlement near Rockville, just south of Zion, with original 1860s structures still standing",
        "The weathered buildings against a backdrop of red cliffs and cottonwood trees have appeared in dozens of films, including Butch Cassidy and the Sundance Kid",
        "A short dirt road leads to the townsite; dogs are welcome to explore the open area around the buildings",
        "The cemetery on the hill tells stories of the settlers who tried to tame this beautiful but harsh landscape",
    ],
    "Grand Canyon Rim Trail": [
        "13-mile paved trail along the South Rim of the Grand Canyon — one of the few pet-friendly trails in the park",
        "Dogs allowed on leash along the entire rim from Hermits Rest to South Kaibab Trailhead",
        "Flat, accessible walking with continuous views into the mile-deep canyon; shuttle stops along the way for easy out-and-back segments",
        "Sunrise and sunset from Hopi Point or Yavapai Point are among the most spectacular views in North America",
    ],
    "Great Basin Highway Overlook": [
        "Elevated viewpoint along US-93 through central Nevada's vast basin-and-range landscape",
        "Sweeping views across empty valleys framed by parallel mountain ranges stretching to the horizon in every direction",
        "The quintessential Great Basin panorama — big sky, sagebrush, and mountains as far as the eye can see",
        "A good leg-stretch stop on the long drive through one of the least-populated corridors in the lower 48",
    ],
    "Great Basin Highway Views": [
        "The long, straight stretches of US-93 through central Nevada offer some of the most dramatic basin-and-range scenery in the West",
        "Mountain ranges rise abruptly from sagebrush valleys in a pattern that repeats for hundreds of miles",
        "Wild horses, pronghorn, and raptors are common sightings along this remote highway corridor",
        "Pull-offs and cattle guards mark spots where the views are especially sweeping across the wide-open Nevada landscape",
    ],
    "Great Sand Dunes View": [
        "Distant views of North America's tallest sand dunes rising 750 feet against the Sangre de Cristo Mountains in southern Colorado",
        "The dunes are visible from Highway 160 and the San Luis Valley floor — a surreal sight of sand at 8,000 feet elevation",
        "The contrast between the golden dunes, dark mountain backdrop, and flat valley floor is unique in North America",
        "Even from a distance, the scale of the dune field is dramatic — covering 30 square miles at the base of the mountains",
    ],
    "Greenway Trail": [
        "Paved urban trail weaving through Flagstaff along the Rio de Flag — part of the city's extensive FUTS trail network",
        "Connects Wheeler Park, Thorpe Park, and downtown restaurants and shops via a tree-lined corridor",
        "Dog-friendly and flat — perfect for a morning or evening walk through town at 7,000 feet where the air stays cool",
        "The ponderosa pines along the trail give Flagstaff a mountain-town feel unlike any other city on Route 66",
    ],
    "Kanab Creek Walk": [
        "Gentle stroll through the small town of Kanab, Utah — gateway to Zion, Bryce, and Grand Canyon North Rim",
        "The town's sandstone-lined creek runs through the center with cottonwood shade and western storefronts",
        "Kanab bills itself as 'Little Hollywood' — dozens of classic westerns were filmed in the surrounding red-rock landscape",
        "Dog-friendly shops, cafés, and a laid-back vibe make this a perfect overnight stop between parks",
    ],
    "Mojave National Preserve": [
        "1.6-million-acre preserve spanning the gap between Joshua Tree and Death Valley with volcanic cinder cones, sand dunes, and Joshua tree forests",
        "Kelso Depot, a restored 1924 Spanish Revival railroad station, serves as the visitor center in the heart of the preserve",
        "Far less visited than neighboring national parks despite having equally dramatic desert landscapes",
        "The Kelso Dunes, Cinder Cones, and Hole-in-the-Wall offer diverse desert scenery with few other visitors around",
    ],
    "Mojave National Preserve - Cima Road": [
        "Scenic drive through the world's densest Joshua tree forest along Cima Road in the Mojave National Preserve",
        "Thousands of Joshua trees stretch across the volcanic landscape toward the Cima Dome, a gentle granitic rise",
        "The road is paved and dog-friendly at pulloffs — great for a stretch break surrounded by desert solitude",
        "Best in spring when Joshua trees may bloom with clusters of white flowers against the desert sky",
    ],
    "Moqui Cave": [
        "Natural sandstone cave turned roadside museum and gift shop on US-89 just north of Kanab, Utah",
        "Collections include dinosaur tracks, fluorescent minerals that glow under UV light, and Native American artifacts",
        "The cave itself stays cool year-round — a fun, quirky stop that's been operating as a tourist attraction since 1951",
        "A classic example of the roadside Americana attractions that once dotted every western highway",
    ],
    "Morro Rock Vista": [
        "576-foot volcanic plug rising from the shoreline of Morro Bay — one of the Nine Sisters chain of ancient volcanic peaks",
        "A paved walking path circles the rock's base with views of the harbor, fishing boats, and sea otters in the bay",
        "Peregrine falcons nest on the rock's face; the surrounding estuary is a bird sanctuary of national significance",
        "Dog-friendly along the base trail and adjacent Embarcadero; the town's fish-and-chips spots overlook the rock",
    ],
    "Mother Road Brewing Company": [
        "Craft brewery in Flagstaff's historic Southside district, named for the Route 66 corridor that runs through town",
        "Dog-friendly patio with a rotating tap list of Arizona-brewed ales, IPAs, and seasonal specialties",
        "A popular locals' hangout that captures Flagstaff's mix of mountain-town grit and college-town creativity",
        "Food trucks usually parked outside; the interior has a railroad-industrial vibe fitting for a Route 66 brewery",
    ],
    "Panorama Point": [
        "Sweeping viewpoint in Capitol Reef overlooking the Waterpocket Fold, a 100-mile wrinkle in the Earth's crust",
        "From this elevation, the multi-colored layers of the fold are visible stretching south toward Lake Powell",
        "One of the best spots to grasp the geology of Capitol Reef — the entire monocline is laid out below",
        "Accessible via a short gravel road; the overlook itself is a quick walk from the parking area",
    ],
    "Red Canyon Trails": [
        "Network of hiking and biking trails through brilliant red-orange hoodoos along Highway 12 west of Bryce Canyon",
        "Often called 'Little Bryce' — similar formations but far fewer people and free to visit (Dixie National Forest)",
        "The highway passes through two natural tunnels carved in the red rock — a stunning entrance to the area",
        "Dog-friendly trails wind among the hoodoos and through stands of ponderosa pine at 7,400 feet",
    ],
    "Red Rock Canyon": [
        "13-mile scenic loop through towering Aztec sandstone formations just 20 minutes west of the Las Vegas Strip",
        "The red and cream banded cliffs rise 3,000 feet from the desert floor — a dramatic geological showcase of ancient sand dunes turned to stone",
        "Dog-friendly on the scenic drive and several connector trails; mornings are coolest for walking with pets",
        "Petroglyphs, desert tortoises, and wild burros add to the experience; the geology rivals anything in southern Utah",
    ],
    "Sacramento Old Town": [
        "Restored Gold Rush-era waterfront district along the Sacramento River with wooden boardwalks, brick buildings, and the Railroad Museum",
        "The California State Railroad Museum houses 21 restored locomotives and is one of the finest railroad museums in North America",
        "Dog-friendly patios on the boardwalk and along the riverfront promenade; street performers and horse-drawn carriages on weekends",
        "The original western terminus of the Pony Express and transcontinental railroad — history packed into a walkable district",
    ],
    "San Rafael Swell - I-70": [
        "Dramatic geologic uplift visible from Interstate 70 as the highway cuts through tilted layers of sandstone, shale, and limestone",
        "The San Rafael Reef — a jagged wall of Navajo sandstone — runs for 75 miles along the eastern edge of the Swell",
        "Rest areas and pulloffs offer views of the Spotted Wolf Canyon and the multicolored Morrison Formation",
        "One of the most scenic stretches of interstate in the country, yet most drivers pass through without realizing what they're seeing",
    ],
    "San Rafael Swell - I-70 Corridor": [
        "The I-70 corridor through the San Rafael Swell is one of the longest stretches of interstate without services — 106 miles",
        "Geological layers spanning 200 million years are exposed in the road cuts and canyon walls along the drive",
        "Black Dragon Canyon and the Wedge Overlook are accessible via dirt roads branching off the highway",
        "The remoteness itself is part of the experience — vast desert panoramas with almost no development visible",
    ],
    "San Rafael Swell Viewpoint": [
        "Overlook along I-70 where the San Rafael Swell's tilted sandstone layers create a dramatic desert landscape",
        "The multi-colored rock formations range from deep red to cream to gray, exposed by millions of years of erosion",
        "Pull-off parking areas allow you to step out and take in the vast scale of this geological feature",
        "A window into the wild, remote heart of Utah's canyon country — visible from the highway but feeling worlds away",
    ],
    "Sand Mountain Recreation Area": [
        "600-foot-tall sand dune in Churchill County, Nevada — one of the few 'singing' sand dunes in North America",
        "The dune produces a low booming sound when sand avalanches down the steep face, caused by the uniform grain size",
        "Sits in the middle of the Great Basin desert surrounded by sagebrush flats and mountain ranges",
        "A dramatic, unexpected landscape formation visible from US-50 — the Loneliest Road in America",
    ],
    "Santa Fe Plaza Morning Walk": [
        "Historic heart of Santa Fe — the oldest public plaza in the United States, continuously used since 1610",
        "Morning light turns the adobe buildings golden; Native American artisans set up jewelry and pottery under the Palace of the Governors portal",
        "Dog-friendly walking through the plaza, past the cathedral, and along the narrow streets lined with galleries and cafés",
        "The 400-year-old adobe architecture and mountain-town atmosphere create a sense of place unlike anywhere else in the US",
    ],
    "Seven Magic Mountains": [
        "Art installation of seven 30-foot-tall towers of stacked, brightly painted boulders rising from the desert south of Las Vegas",
        "Created by Swiss artist Ugo Rondinone — the fluorescent colors contrast dramatically against the muted desert landscape",
        "Free roadside attraction just off I-15; the towers are visible from the highway and accessible via a short gravel path",
        "One of the most photographed art installations in the American West — best in the golden hour light of early morning or late afternoon",
    ],
    "Springdale Town Walk": [
        "Gateway town to Zion National Park with galleries, restaurants, and outfitter shops lining the main street beneath towering red cliffs",
        "The town itself feels like an extension of the park — sandstone walls rise directly behind the buildings on both sides",
        "Dog-friendly sidewalks and patios; several restaurants have outdoor seating with views of the Watchman and other Zion formations",
        "A pleasant evening stroll after a day in the park, with the cliffs glowing red-orange in the setting sun",
    ],
    "Tehachapi Wind Farm": [
        "One of the earliest and largest wind energy developments in the world, with thousands of turbines blanketing the Tehachapi Pass",
        "The turbines range from small 1980s-era models to massive modern units, creating a surreal industrial landscape against golden hills",
        "Visible from Highway 58 and the Tehachapi-Willow Springs Road — a dramatic gateway between the Central Valley and Mojave Desert",
        "Generates enough clean energy to power 350,000 homes; the scale of the installation is best appreciated from the surrounding ridgelines",
    ],
    "Tonopah Historic Mining Park": [
        "Open-air museum at the original 1900 silver strike site that turned Tonopah into Nevada's biggest boomtown",
        "Walk through original mine headframes, ore bins, and processing equipment perched on the hillside above town",
        "Self-guided trails lead past mining artifacts with interpretive signs explaining the boom-and-bust cycle that shaped the town",
        "Views from the hilltop span the entire Tonopah valley — the same view miners saw when they struck the second-richest silver deposit in Nevada history",
    ],
    "Vail Pass Summit": [
        "10,666-foot mountain pass on I-70 between Copper Mountain and Vail — one of the highest points on the US Interstate system",
        "Rest area at the summit offers stunning views of the Gore Range and surrounding White River National Forest",
        "The Vail Pass Recreation Trail connects here — a paved bike path that descends to Vail following Ten Mile Creek",
        "Snow can linger at the summit well into June; the alpine scenery is a dramatic contrast to the desert landscapes further west",
    ],
    "Valley of Fire State Park": [
        "Nevada's oldest and largest state park, featuring brilliant red Aztec sandstone formations that appear to be on fire in the sunlight",
        "2,000-year-old Ancestral Puebloan petroglyphs at Atlatl Rock and Mouse's Tank trail are easily accessible",
        "The Fire Wave trail leads to a stunning formation of red, pink, and white banded sandstone resembling frozen waves",
        "Dog-friendly on roads and at viewpoints; the rocks glow most intensely at sunrise and sunset",
    ],
    "Wahweap Overlook Trail": [
        "Short trail near Wahweap Marina offering panoramic views of Lake Powell's turquoise water against red and white sandstone",
        "The view encompasses the dam, Wahweap Bay, and the distant Kaiparowits Plateau on the horizon",
        "Easy walking on packed earth — perfect for an evening stroll to watch sunset paint the cliffs above the lake",
        "One of the most accessible overlooks of Lake Powell without needing a boat or backcountry permit",
    ],
    "Zion Canyon Scenic Drive": [
        "6-mile road following the Virgin River through the heart of Zion Canyon between 2,000-foot sandstone walls",
        "Shuttle-only in peak season, but the road itself is a destination — every turn reveals another monumental cliff face",
        "Major stops include the Court of the Patriarchs, Big Bend, and the Temple of Sinawava at the road's end",
        "The scale of the canyon is hard to overstate — the Great White Throne and Angels Landing tower overhead at every viewpoint",
    ],
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
            thumb_url = info.get("thumburl") or info.get("url", "")
            if "image" not in mime or "svg" in mime:
                continue
            if width < 400 or height < 300:
                continue
            if ".tif" in thumb_url.lower():
                continue
            if thumb_url:
                urls.append(thumb_url)
        return urls[:PHOTOS_PER_ATTRACTION]
    except Exception as e:
        print(f"    API error: {e}")
        return []


def main():
    # Load existing attraction data
    with open(f"{DATA_DIR}/attraction-data.json") as f:
        existing = json.load(f)

    # Load new route proposals to find all attractions
    with open(f"{DATA_DIR}/route-proposals.json") as f:
        proposals = json.load(f)

    # Collect all attraction names and types from new routes
    new_attractions = {}
    for route in proposals["routes"]:
        for day in route["days"]:
            for hl in day.get("highlights", []):
                if hl["name"] not in existing and hl["name"] not in new_attractions:
                    new_attractions[hl["name"]] = hl["type"]

    if not new_attractions:
        print("No new attractions to fetch!")
        return

    print(f"Found {len(new_attractions)} new attractions to fetch")
    print(f"Estimated time: ~{len(new_attractions)} seconds\n")

    success = 0
    partial = 0
    failed = 0
    total = len(new_attractions)

    for i, (name, atype) in enumerate(new_attractions.items(), 1):
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

        desc = DESCRIPTIONS.get(name, [name])

        existing[name] = {
            "photos": urls,
            "type": atype,
            "desc": desc,
        }

        print(f" — {status} ({len(urls)} photos)")

        if i < total:
            time.sleep(RATE_LIMIT)

    # Save merged result
    outpath = f"{DATA_DIR}/attraction-data.json"
    with open(outpath, "w") as f:
        json.dump(existing, f, indent=2)

    total_entries = len(existing)
    total_photos = sum(len(v["photos"]) for v in existing.values())
    size_mb = len(json.dumps(existing)) / 1024 / 1024

    print(f"\nDone! {success} OK, {partial} partial, {failed} failed out of {total} new attractions")
    print(f"Total attractions in data: {total_entries}")
    print(f"Total photos: {total_photos}")
    print(f"Output: {outpath} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
