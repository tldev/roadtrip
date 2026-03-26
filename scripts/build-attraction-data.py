#!/usr/bin/env python3
"""
Combine fetched Wikimedia Commons images with expanded descriptions.
Outputs data/attraction-data.json for the routes.html showcase.
"""

import json

DESCRIPTIONS = {
    # ═══════════════════ ROUTE 1: The Desert Crossing ═══════════════════
    "Paso Robles Wine Country": [
        "Central Coast wine destination with 200+ wineries and tasting rooms spread across rolling hills and oak-studded valleys",
        "Dog-friendly patios at many wineries — try Tablas Creek, Justin, or Eberle for laid-back outdoor tastings",
        "Known for bold Cabernet Sauvignon, Zinfandel, and Rhône-style blends; the terroir rivals Napa at half the pretension",
        "Downtown square has craft breweries, olive oil shops, and farm-to-table restaurants worth a stop"
    ],
    "Tehachapi Loop Railroad": [
        "National Historic Civil Engineering Landmark where freight trains spiral 77 feet upward over themselves in a complete loop",
        "Best viewed from Woodford-Tehachapi Road — long BNSF trains actually cross over their own tail as they climb the Tehachapi Pass",
        "Built in 1876 to conquer the steep grade between the San Joaquin Valley and the Mojave Desert",
        "Trains run frequently; you can often catch one within 20-30 minutes of arriving at the viewpoint"
    ],
    "Wind Farm Fields": [
        "Thousands of wind turbines stretching across the Tehachapi Pass — one of the earliest and largest wind farms in the world",
        "The turbines range from vintage 1980s models to massive modern units, creating a surreal industrial-meets-nature landscape",
        "Best viewed from the highway as you descend from the mountains into the Mojave Desert",
        "Generates enough electricity to power 350,000 homes — a striking visual gateway between Central and Southern California"
    ],
    "Roy's Cafe Amboy": [
        "Iconic Route 66 roadside stop with a classic 1950s neon sign and Googie-architecture gas station in the Mojave Desert",
        "The surrounding town of Amboy is essentially a ghost town — Roy's stands alone against vast desert emptiness",
        "Recently restored and reopened for fuel and cold drinks; the sign is one of the most photographed on all of Route 66",
        "Nearby Amboy Crater offers a short hike to a volcanic cinder cone visible from the road"
    ],
    "Route 66 Museum Kingman": [
        "Housed in the 1907 Powerhouse building, this museum features life-size dioramas recreating every era of Route 66 history",
        "Vintage cars, neon signs, and a detailed mural-lined walkway trace the Mother Road from Chicago to Santa Monica",
        "Kingman is the hub of the longest remaining driveable stretch of original Route 66 in Arizona",
        "Free Route 66 walking tour maps available — downtown still has original 1940s-50s neon signs"
    ],
    "Hualapai Mountain Park": [
        "Pine-forested mountain park rising to 8,417 feet — a cool escape from the desert heat below in Kingman",
        "Dog-friendly trails wind through ponderosa pine and granite boulders with views stretching into three states",
        "Historic stone cabins built by the CCC in the 1930s are available to rent for an overnight stay",
        "Wildlife includes mule deer, elk, and wild turkeys; fall brings golden aspen color to the upper elevations"
    ],
    "Oak Creek Canyon Scenic Drive": [
        "14-mile scenic highway carved between towering red and white sandstone walls — often called Arizona's mini Grand Canyon",
        "The road descends 2,000 feet through switchbacks with pulloffs offering dramatic canyon views at every turn",
        "Slide Rock State Park along the route features a natural waterslide carved into red sandstone creek bed",
        "Fall foliage in October transforms the canyon with reds, oranges, and yellows against the red rock walls"
    ],
    "Bell Rock Pathway": [
        "Easy 3.6-mile loop trail circling the iconic bell-shaped red rock butte, one of Sedona's most recognizable landmarks",
        "Known as one of Sedona's four main vortex sites — a spot believed to radiate subtle earth energy",
        "Trail is wide and flat, perfect for dogs on leash, with panoramic views of Courthouse Butte and the surrounding red rock formations",
        "Best at sunrise or sunset when the sandstone glows deep orange-red"
    ],
    "Tlaquepaque Arts Village": [
        "Spanish colonial-style arts and crafts village modeled after a traditional Mexican village in Guadalajara",
        "Over 40 galleries and shops featuring Southwestern art, sculpture, jewelry, and handcrafted goods",
        "Sycamore-shaded courtyards with fountains, vine-covered archways, and hand-laid tile throughout",
        "Dog-friendly outdoor areas; several restaurants and tasting rooms with patio seating along Oak Creek"
    ],
    "West Fork Oak Creek Trail": [
        "One of Arizona's most popular hikes — a lush, shaded canyon trail that criss-crosses Oak Creek 13 times",
        "Towering red and white canyon walls frame a riparian forest of maple, oak, and fir trees",
        "The first 3 miles are an easy, well-maintained path; beyond that it becomes a creek-walking adventure",
        "Spectacular fall color in late October — one of the few places in Arizona with true autumn foliage"
    ],
    "Airport Mesa Overlook": [
        "360-degree panoramic viewpoint perched on a mesa overlooking all of Sedona's red rock formations",
        "Famous sunset spot — watch the rocks shift from red to deep purple as the sun drops below the horizon",
        "One of Sedona's four main vortex sites; the loop trail is short (3.3 miles) but moderately steep",
        "On clear days you can see the San Francisco Peaks near Flagstaff, 30 miles to the north"
    ],
    "Rancho Sedona RV Park": [
        "Shaded RV park nestled along Oak Creek in the heart of Sedona, with red rock views from every site",
        "Direct creek access for wading and cooling off; large grassy areas for dogs to enjoy",
        "Walking distance to Tlaquepaque Arts Village, galleries, and restaurants in uptown Sedona",
        "One of the few campgrounds with full hookups right in town, surrounded by towering cottonwood trees"
    ],
    "Page Springs Cellars": [
        "Arizona's premier winery tucked in the Verde Valley along Oak Creek, specializing in Rhône and Spanish varietals",
        "Dog-friendly outdoor patio overlooking the creek with cottonwood shade and vineyard views",
        "Part of the Verde Valley Wine Trail — pair a tasting with nearby Javelina Leap or Alcantara Vineyards",
        "The region's unique high-desert terroir at 3,500 feet produces wines with distinctive mineral character"
    ],
    "Standin' on the Corner Park Winslow": [
        "Tribute to the Eagles' 'Take It Easy' — a bronze statue and mural at the corner of Route 66 and Kinsley Ave",
        "The iconic flatbed Ford from the song lyric is parked permanently at the corner for photos",
        "La Posada Hotel across the street is a beautifully restored 1929 Fred Harvey railroad hotel worth exploring",
        "A must-stop for classic rock fans driving Route 66; the park also hosts live music events in season"
    ],
    "Petrified Forest National Park": [
        "225-million-year-old petrified logs scattered across a painted desert landscape of banded badlands and mesas",
        "The Crystal Forest trail has the densest concentration of jewel-toned petrified wood — some logs are six feet across",
        "The Painted Desert stretches to the horizon in layers of red, orange, purple, and grey Chinle Formation clay",
        "Ancient Puebloan petroglyphs at Newspaper Rock and the partially excavated Puerco Pueblo ruins"
    ],
    "El Rancho Hotel Gallup": [
        "Historic 1937 hotel where golden-age Hollywood stars stayed while filming westerns in the area",
        "Autographed portraits of John Wayne, Humphrey Bogart, Katharine Hepburn, and Ronald Reagan line the lobby walls",
        "Distinctive rustic-Southwest architecture with massive log beams and a neon sign visible from I-40",
        "Still operating as a hotel — the restaurant and bar are decorated with original movie memorabilia"
    ],
    "Albuquerque Old Town": [
        "Historic Spanish colonial plaza founded in 1706, with adobe buildings surrounding a tree-shaded central square",
        "Over 100 shops, galleries, and restaurants specializing in traditional New Mexican cuisine and Native American art",
        "San Felipe de Neri Church, built in 1793, is one of the oldest surviving structures in Albuquerque",
        "Nearby Indian Pueblo Cultural Center and the ABQ BioPark are both worth a visit"
    ],
    "Petroglyph National Monument": [
        "Over 24,000 petroglyphs carved into volcanic basalt along a 17-mile escarpment on Albuquerque's west side",
        "Boca Negra Canyon has the easiest access with three short trails showcasing hundreds of carvings from 400-700 years ago",
        "Images include animals, people, crosses, and abstract spirals carved by ancestral Pueblo peoples and early Spanish settlers",
        "Rinconada Canyon offers a longer, quieter 2.2-mile loop with fewer crowds and more petroglyphs per step"
    ],
    "Fishers Peak State Park": [
        "Colorado's newest state park (2020) centered on the dramatic 9,633-foot mesa that dominates the Trinidad skyline",
        "The mesa's flat top and sheer cliffs are visible for miles — a landmark for travelers on the Santa Fe Trail",
        "Currently being developed with new trails; the scenery combines shortgrass prairie with volcanic geology",
        "Rich history as a waypoint for the Santa Fe Trail, Spanish explorers, and the Ute and Apache peoples"
    ],
    "Spanish Peaks Vista": [
        "Twin volcanic peaks rising 7,000 feet above the plains — known to the Ute as 'Huajatolla' (Breasts of the Earth)",
        "Great Dikes of the Spanish Peaks radiate outward like stone walls up to 100 feet tall, formed by ancient magma intrusions",
        "Visible for over 100 miles in every direction; they served as landmarks for Native peoples, Spanish explorers, and pioneers",
        "The Highway of Legends (CO-12) winds through the area with pulloffs for stunning views of both peaks"
    ],
    "Pikes Peak View": [
        "America's Mountain at 14,115 feet — the peak that inspired 'America the Beautiful' in 1893",
        "The new Pikes Peak Summit Visitor Center at the top offers panoramic views into four states on clear days",
        "Visible from over 100 miles away on the Great Plains; you can drive, bike, or take the Cog Railway to the summit",
        "Garden of the Gods at the base frames Pikes Peak perfectly between towering red sandstone formations"
    ],

    # ═══════════════════ ROUTE 2: The Grand Canyon Route ═══════════════════
    "Bearizona Wildlife Park": [
        "Drive-through wildlife park in Williams, AZ where black bears, wolves, bison, and other North American animals roam in natural habitats",
        "The drive-through section lets you see bears, bison, and wolves from your car; a walk-through area has smaller animals and birds",
        "Baby animal season in spring features bear cubs, wolf pups, and baby bison — popular with families",
        "Located on the way to Grand Canyon, making it a natural stop on the Williams-to-South Rim drive"
    ],
    "Route 66 Historic Downtown Williams": [
        "The last town on Route 66 to be bypassed by Interstate 40 (1984) — the historic downtown still has original neon and diners",
        "Gateway to the Grand Canyon via the scenic Grand Canyon Railway, a vintage steam train that's run since 1901",
        "Original Route 66 motels, soda fountains, and souvenir shops line the main drag with classic Americana charm",
        "Cruisin' on Route 66 car show and nightly stroller walks keep the Mother Road spirit alive"
    ],
    "Mather Point": [
        "The first and most popular Grand Canyon viewpoint on the South Rim — your initial jaw-dropping glimpse into the abyss",
        "Two paved overlooks extend over the rim with unobstructed views spanning 30+ miles of layered canyon",
        "Directly adjacent to the visitor center and connected to the Rim Trail for easy access",
        "Best at sunrise when the first light paints the canyon walls in golden hues and the Colorado River sparkles below"
    ],
    "Rim Trail": [
        "13-mile paved path along the South Rim of the Grand Canyon connecting all major viewpoints from Hermit's Rest to South Kaibab",
        "Mostly flat and wheelchair-accessible between the Village and Mather Point, with stunning views the entire way",
        "Free shuttle buses run along the route, so you can walk one direction and ride back",
        "Every few hundred yards offers a different perspective — the canyon's scale is impossible to capture in a single view"
    ],
    "Desert View Watchtower": [
        "70-foot stone watchtower designed by Mary Colter in 1932, modeled after ancient Puebloan towers, with 360-degree views",
        "Interior murals by Hopi artist Fred Kabotie depict Hopi legends and the history of the Grand Canyon region",
        "Highest point on the South Rim at 7,522 feet — on clear days you can see the Painted Desert and Navajo Mountain",
        "The easternmost South Rim viewpoint, with dramatic views of the canyon's widest section and the Colorado River below"
    ],
    "Shoshone Point": [
        "A hidden Grand Canyon viewpoint reached by a quiet 1-mile walk through ponderosa pine forest — no crowds, no shuttle",
        "The point itself juts out into the canyon with 270-degree views and a peaceful, almost private atmosphere",
        "Unlike other South Rim overlooks, it's not on any shuttle route — most visitors don't know it exists",
        "Popular spot for picnics and photography; the silence is remarkable compared to the busy main viewpoints"
    ],
    "Mather Campground": [
        "The primary South Rim campground with 327 sites nestled in a ponderosa pine forest just minutes from the rim",
        "Sites are well-spaced and shaded; the camp store, showers, and laundry are on-site for convenience",
        "Walking distance to the Rim Trail, Mather Point, and the Village with restaurants and shops",
        "Reservations open 6 months in advance and sell out fast — book early for peak season (May-September)"
    ],
    "Hopi Point Sunset": [
        "Widely considered the best sunset viewpoint on the South Rim — a wide promontory with views spanning 90+ miles of canyon",
        "Watch the canyon walls cycle through gold, orange, deep red, and purple as the sun sets behind the North Rim",
        "One of the few spots where you can see the Colorado River from the South Rim, winding 5,000 feet below",
        "The Hermit Road shuttle drops you right at the point; arrive 30-45 minutes early in season for a good spot"
    ],
    "Grand Canyon Dark Sky Park": [
        "The Grand Canyon became an International Dark Sky Park in 2019 — some of the darkest skies near a major US attraction",
        "On moonless nights the Milky Way arcs brilliantly over the canyon, with 7,000+ stars visible to the naked eye",
        "Annual Star Party in June brings astronomers with large telescopes for public viewing on the South Rim",
        "The combination of dark skies and canyon acoustics — absolute silence broken only by distant rapids — is unforgettable"
    ],
    "Cameron Trading Post": [
        "Historic Navajo trading post established in 1916, perched on the rim of the Little Colorado River Gorge",
        "The gallery features museum-quality Navajo rugs, turquoise jewelry, kachina dolls, and pottery",
        "The dining room serves excellent Navajo tacos and fry bread — a perfect lunch stop between the Grand Canyon and Monument Valley",
        "A pedestrian suspension bridge crosses the Little Colorado River gorge — the turquoise water at the bottom is striking"
    ],
    "Moenkopi Dinosaur Tracks": [
        "Real 200-million-year-old dinosaur footprints preserved in sandstone near Tuba City on the Navajo Nation",
        "Navajo guides lead you across the rock to identify three-toed Dilophosaurus tracks, some with skin impressions still visible",
        "Free to visit (tips appreciated); the guides share both scientific context and Navajo oral traditions about the tracks",
        "The tracks are remarkably well-preserved — you can clearly see individual toe pads and claw marks"
    ],
    "Monument Valley": [
        "Towering sandstone buttes rising 1,000 feet from the desert floor — the landscape that defined the American West in film",
        "The 17-mile Valley Drive loop passes the iconic Mittens, Merrick Butte, and John Ford's Point overlook",
        "Managed by the Navajo Nation — Navajo-guided tours access restricted areas including Mystery Valley and Hunts Mesa",
        "Best photographed at sunrise or sunset when the buttes glow deep red against a vast sky"
    ],
    "Four Corners Monument": [
        "The only place in the US where four state borders meet — stand in Arizona, New Mexico, Utah, and Colorado simultaneously",
        "A bronze marker set into a granite platform marks the exact intersection of the four states",
        "Navajo and Ute vendors sell handmade jewelry, pottery, and fry bread at stalls surrounding the monument",
        "The surrounding landscape is stark high desert — a genuine middle-of-nowhere feeling"
    ],
    "Mesa Verde National Park": [
        "Over 600 ancient cliff dwellings built into sandstone alcoves by the Ancestral Puebloans between 600 and 1300 AD",
        "Cliff Palace, the largest cliff dwelling in North America, has 150 rooms and 23 kivas tucked under a massive overhang",
        "Ranger-led tours descend ladders into the alcoves for up-close views of the architecture and ancient plaster walls",
        "The mesa-top loop drive passes several overlooks and surface ruins showing the evolution of Puebloan construction"
    ],
    "Durango Dog Park": [
        "Durango's off-leash dog park along the Animas River with mountain views and plenty of room to run",
        "The town itself is a charming historic mining community with a walkable Main Avenue full of shops and restaurants",
        "Nearby Durango & Silverton Narrow Gauge Railroad runs historic steam trains through the San Juan Mountains",
        "Surrounded by San Juan National Forest — trails for every ability level within a short drive"
    ],
    "Animas River Trail": [
        "7-mile paved trail following the Animas River through downtown Durango — perfect for walking, running, or biking with dogs",
        "The trail connects Rotary Park to Dallabetta Park with river access points for wading along the way",
        "Views of the surrounding San Juan Mountains and historic railroad bridges crossing overhead",
        "Popular with locals year-round; in summer the river is busy with kayakers, tubers, and fly fishermen"
    ],
    "Carver Brewing Company": [
        "Durango's original craft brewery, operating since 1988 in a historic downtown building on Main Avenue",
        "Known for their Raspberry Wheat Ale and Jack Rabbit Pale Ale — the outdoor patio is dog-friendly",
        "The breakfast menu is locally famous; they roast their own coffee and serve hearty mountain-town portions",
        "A Durango institution — the kind of place where locals and travelers mix over good beer and live music"
    ],
    "Smelter Mountain Trail": [
        "Short but steep trail climbing to an overlook above Durango with sweeping views of the Animas Valley and the La Plata Mountains",
        "Named for the historic smelter that once processed ore from the San Juan mining district",
        "The summit panorama includes downtown Durango, the Animas River, and snow-capped peaks on the skyline",
        "Best at sunset when the alpenglow lights up the surrounding peaks in pink and gold"
    ],
    "Million Dollar Highway": [
        "25 miles of dramatic switchbacks, sheer cliff edges, and 11,000-foot passes connecting Silverton to Ouray — no guardrails",
        "Named either for the cost to build or the million-dollar views — every mile offers jaw-dropping San Juan Mountain scenery",
        "Part of the San Juan Skyway, one of America's most scenic drives, passing abandoned mines and waterfalls",
        "Fall color in late September turns the mountainsides into walls of gold aspen against dark evergreen and grey rock"
    ],
    "Silverton": [
        "Tiny former mining town at 9,318 feet in the San Juan Mountains, preserved almost exactly as it looked in the 1880s",
        "The entire downtown is a National Historic Landmark — wooden boardwalks, Victorian storefronts, and saloons line Blair Street",
        "End of the line for the Durango & Silverton Narrow Gauge Railroad; the steam train's arrival is a daily event",
        "Surrounded by 13,000-foot peaks and dozens of 4WD roads leading to ghost towns and alpine lakes"
    ],
    "Black Canyon of the Gunnison": [
        "One of the steepest, narrowest, and most dramatic gorges in North America — the Gunnison River drops 2,700 feet in 48 miles",
        "The Painted Wall, Colorado's tallest cliff at 2,250 feet, is streaked with veins of pink pegmatite that glow at sunset",
        "The South Rim Drive offers 12 viewpoints, each revealing a different angle of the impossibly deep, dark chasm",
        "The canyon is so narrow (40 feet at the Narrows) that sunlight reaches the bottom for only 33 minutes a day in some spots"
    ],

    # ═══════════════════ ROUTE 3: Utah's Mighty Five ═══════════════════
    "Alabama Hills": [
        "Otherworldly landscape of rounded granite boulders and arches at the foot of Mount Whitney and the Eastern Sierra escarpment",
        "Backdrop for hundreds of Hollywood westerns, sci-fi films, and TV shows — Movie Road passes the most iconic formations",
        "Mobius Arch frames a perfect view of Mount Whitney through its opening — best photographed at dawn",
        "Free dispersed camping on BLM land with unobstructed views of the Sierra crest — one of California's best free campsites"
    ],
    "Mobius Arch": [
        "Natural granite arch in the Alabama Hills that perfectly frames Mount Whitney, the tallest peak in the Lower 48",
        "A short 0.5-mile trail leads to the arch; the loop passes several other interesting rock formations",
        "Best photographed at dawn when Mount Whitney catches the first golden light through the arch's opening",
        "The surrounding boulder field creates a maze-like landscape that looks like another planet"
    ],
    "Mt. Whitney Portal Road": [
        "Steep mountain road climbing 3,000 feet in 13 miles from the Owens Valley to Whitney Portal at 8,374 feet",
        "Dramatic views of the Eastern Sierra escarpment — the mountain wall rises nearly vertically from the desert floor",
        "Whitney Portal has a small store, campground, and the trailhead for the 22-mile round-trip to the 14,505-foot summit",
        "Even if you don't hike Whitney, the portal area has short trails, waterfalls, and stunning alpine scenery"
    ],
    "Bishop, CA": [
        "Small Eastern Sierra town known as the gateway to the Buttermilk Boulders, world-class rock climbing, and High Sierra trailheads",
        "The Owens Valley setting delivers 360-degree views of the Sierra Nevada and White Mountains — big sky country",
        "Erick Schat's Bakkery is a mandatory stop for their famous sheepherder bread and pastries",
        "Mule Days celebration in May is the town's signature event — Bishop takes its pack mule heritage seriously"
    ],
    "Tonopah Stargazing Park": [
        "Dedicated dark-sky park in one of the most remote towns in Nevada, far from any city light pollution",
        "The Milky Way is so bright here it casts shadows — on a clear night you can see 7,000+ stars with the naked eye",
        "The park has telescope pads, informational panels, and a sheltered viewing area designed for astrophotography",
        "Tonopah sits at the intersection of US-6 and US-95 — a beautifully desolate crossroads in the Nevada desert"
    ],
    "Mizpah Hotel": [
        "Historic 1907 five-story hotel that was once the tallest building in Nevada — beautifully restored with period furnishings",
        "Known as one of America's most haunted hotels; the 'Lady in Red' ghost story has been featured on TV shows",
        "The basement bar and Jack Dempsey Room restaurant serve craft cocktails and steaks in a turn-of-century atmosphere",
        "A surprising gem in tiny Tonopah — the level of restoration and period detail rivals boutique hotels in major cities"
    ],
    "Tonopah Brewing Company": [
        "Craft brewery in the heart of Tonopah serving locally brewed beers in a casual, traveler-friendly atmosphere",
        "A welcome oasis on the long stretch of US-6/US-95 between Reno and Las Vegas — cold beer in the middle of nowhere",
        "The taproom has a laid-back desert vibe with local art and mining-history decor",
        "Try the local specialties alongside a flight; the brewery is a gathering spot for the small but spirited Tonopah community"
    ],
    "Zion National Park": [
        "Towering sandstone cliffs of cream, pink, and red rise 2,000+ feet above the Virgin River in this narrow desert canyon",
        "Angels Landing is the iconic 5.4-mile hike with chain-assisted sections along a knife-edge ridge — not for the faint of heart",
        "The Narrows lets you wade through the Virgin River between 1,000-foot canyon walls — one of the world's great slot canyons",
        "The scenic drive through Zion Canyon is shuttle-only in season; the human-powered atmosphere makes it feel like a European park"
    ],
    "Pa'rus Trail": [
        "Easy 3.5-mile paved trail along the Virgin River in Zion — one of only two trails in the park that allows dogs and bikes",
        "Crosses the river on multiple bridges with views of the Watchman, Bridge Mountain, and the Towers of the Virgin",
        "Flat and shaded by cottonwood trees; a perfect morning or evening walk without the crowds of the canyon trails",
        "Connects the Visitor Center to Canyon Junction, giving you postcard views of Zion's main canyon walls"
    ],
    "Bryce Canyon National Park": [
        "Thousands of red, orange, and white hoodoo spires packed into natural amphitheaters carved by frost and erosion",
        "The Navajo Loop and Queen's Garden trails descend into the hoodoo forest — like walking through a Dr. Seuss landscape",
        "Sunrise Point and Sunset Point live up to their names; the hoodoos change color dramatically with the angle of light",
        "At 8,000-9,000 feet elevation, Bryce is significantly cooler than other Utah parks — and has some of the darkest skies in the US"
    ],
    "Scenic Byway 12": [
        "124 miles of the most spectacular driving in Utah — winding from Bryce Canyon through red rock canyons to Capitol Reef",
        "The Hogback section near Escalante rides a narrow ridge with sheer drops on both sides and 360-degree canyon views",
        "Passes through the tiny towns of Escalante, Boulder, and Torrey — each with their own character and local restaurants",
        "Designated an All-American Road — one of only 31 in the country — for scenery that can't be found anywhere else"
    ],
    "Red Canyon": [
        "Brilliant red hoodoos and arches lining Highway 12 west of Bryce Canyon — a free preview of what's to come",
        "Several short trails weave through the formations; the Arches Trail leads to two natural windows in the red rock",
        "The canyon walls are so close to the road that a tunnel was carved through them — a dramatic entrance",
        "Often overlooked because of its famous neighbor, but the color intensity here rivals Bryce with a fraction of the crowds"
    ],
    "Capitol Reef National Park": [
        "100-mile wrinkle in the earth's crust called the Waterpocket Fold — a monocline of tilted, colorful rock layers",
        "The Fruita Historic District has orchards planted by Mormon pioneers in the 1880s — pick cherries, apples, and peaches in season",
        "Petroglyphs, pictographs, and pioneer-era inscriptions are scattered throughout the park's sandstone walls",
        "Capitol Dome, a white Navajo Sandstone formation resembling the US Capitol, gives the park its name"
    ],
    "Goblin Valley State Park": [
        "Thousands of mushroom-shaped sandstone formations (hoodoos called 'goblins') eroded into a surreal alien landscape",
        "Unlike most parks, you're encouraged to wander freely among the formations — climbing and exploring is allowed",
        "Used as a filming location for Galaxy Quest and other sci-fi productions — it genuinely looks like another planet",
        "Designated International Dark Sky Park; the remoteness makes it one of Utah's best stargazing spots"
    ],
    "Dead Horse Point State Park": [
        "Dramatic overlook 2,000 feet above a gooseneck bend of the Colorado River — the view rivals Grand Canyon for sheer wow factor",
        "The point's name comes from a legend about wild mustangs corralled on the narrow mesa and left to perish",
        "The famous potash evaporation ponds below the overlook create geometric patches of brilliant blue and green",
        "Used as a filming location for the final scene of Thelma & Louise and the opening of Mission: Impossible 2"
    ],
    "Corona Arch Trail": [
        "Moderate 3-mile round-trip trail to a massive 140-foot-wide natural arch — one of the largest in the Moab area",
        "The trail crosses slickrock with cable-assisted sections and a short ladder — adventurous without being dangerous",
        "Corona Arch is large enough to fit a 747 underneath and far less crowded than Arches National Park",
        "Also passes Bowtie Arch and Pinto Arch along the way — three arches for the effort of one hike"
    ],
    "Arches National Park": [
        "Over 2,000 natural stone arches in a concentrated area — the densest collection on Earth, including the iconic Delicate Arch",
        "Delicate Arch stands alone on the edge of a sandstone bowl with the La Sal Mountains behind — Utah's most photographed landmark",
        "Landscape Arch in Devils Garden spans 306 feet — one of the longest natural arches in the world and still slowly eroding",
        "The Windows Section has massive arches you can walk right up to, plus a parade of fins and balanced rocks"
    ],
    "Canyonlands Island in the Sky": [
        "Vast mesa-top district of Canyonlands with 360-degree views into 1,000-foot-deep canyons carved by the Colorado and Green rivers",
        "Grand View Point overlook lets you see 100 miles of canyon country — it feels like standing on top of the world",
        "Mesa Arch at sunrise is a photographer's pilgrimage — the dawn light glows orange through the arch and illuminates the canyon below",
        "The White Rim Road, a 100-mile 4WD loop 1,200 feet below the rim, is one of the great off-road adventures in the American West"
    ],
    "Grandstaff Trail": [
        "4.2-mile round-trip hike through a narrow side canyon of the Colorado River to Morning Glory Natural Bridge, the 6th-largest in the US",
        "The trail follows a perennial creek through a red rock canyon — you'll cross the stream several times on stepping stones",
        "Morning Glory Bridge is tucked in an alcove at the end — a 243-foot span draped with hanging gardens and maidenhair fern",
        "Dog-friendly on leash; one of the best moderate canyon hikes in the Moab area"
    ],
    "Moab KOA": [
        "Full-service campground on the banks of the Colorado River just south of Moab with mountain and canyon views",
        "Convenient base camp for Arches and Canyonlands national parks, both within 30 minutes",
        "Pool, hot tub, and river access for cooling off after a day of desert hiking and 4WD exploration",
        "The surrounding landscape of red cliffs and the river make it one of the more scenic KOA locations in the country"
    ],
    "Glenwood Canyon": [
        "12-mile stretch of Interstate 70 carved through a 1,300-foot-deep canyon along the Colorado River — an engineering marvel",
        "The highway features 40 bridges, a half-mile tunnel, and elevated roadway sections built to minimize impact on the canyon",
        "The Glenwood Canyon Bike Path runs the entire length — a stunning separated path along the river below the highway",
        "Hanging Lake, a short but steep hike to a turquoise pool fed by a waterfall, is the canyon's crown jewel (reservations required)"
    ],
    "Vail Village": [
        "Bavarian-style alpine village at 8,150 feet in the heart of the Colorado Rockies, charming year-round",
        "In summer, the ski slopes become hiking and mountain biking trails with wildflower meadows and gondola access",
        "The cobblestone pedestrian village has upscale shops, galleries, and restaurants — no cars allowed in the core",
        "Free summer concerts, farmers markets, and outdoor festivals make it worth a stop even if you're just passing through"
    ],
    "Eisenhower Tunnel": [
        "The highest point on the US Interstate system at 11,158 feet — a 1.7-mile tunnel bored through the Continental Divide",
        "Named for President Eisenhower, who championed the Interstate Highway System; the tunnel took 10 years to build",
        "The approach through Loveland Pass offers optional scenic driving above treeline with alpine tundra and big mountain views",
        "On the west side, the tunnel emerges into the broad Summit County valley with views of ski resorts and fourteeners"
    ],

    # ═══════════════════ ROUTE 4: The Southern Sun ═══════════════════
    "Hearst Castle Vista Point": [
        "Hilltop estate built by William Randolph Hearst between 1919-1947 — a 165-room palatial complex above the Pacific Coast",
        "The Neptune Pool, Roman Temple facade, and Casa Grande are architectural fantasies mixing Mediterranean and Moorish styles",
        "Tours run daily and include the ornate indoor Roman Pool with gold-leaf mosaic tiles and marble statuary",
        "Even without a tour, the coastal views from the surrounding hills and the elephant seal colony at Piedras Blancas are spectacular"
    ],
    "Morro Rock & Morro Bay": [
        "576-foot volcanic plug rising from the harbor — one of the Nine Sisters, a chain of ancient volcanic peaks along the coast",
        "The bay is home to sea otters, harbor seals, and a great blue heron rookery visible from the Embarcadero waterfront",
        "Fresh seafood restaurants line the harborfront; the fish and chips here rival anything on the California coast",
        "Morro Bay State Park nearby has a marina, museum, and eucalyptus-grove campground overlooking the bay"
    ],
    "Santa Barbara Waterfront": [
        "Red-tile-roofed Mediterranean-style city between the Santa Ynez Mountains and the Pacific — the 'American Riviera'",
        "Stearns Wharf, built in 1872, extends over the ocean with restaurants, shops, and panoramic coastal views",
        "The waterfront bike path connects East Beach, West Beach, and Leadbetter Beach — all dog-friendly before 10 AM",
        "State Street runs uphill from the wharf through the Funk Zone wine tasting district to the historic downtown"
    ],
    "Route 66 Dog Park Kingman": [
        "Off-leash dog park in Kingman along the original Route 66 corridor, a welcome stretch break on a driving day",
        "Kingman sits at the heart of the longest remaining driveable stretch of Route 66 in Arizona",
        "The nearby Mohave Museum of History and Arts covers the region's mining, railroad, and Route 66 heritage",
        "A practical stop with shade structures and water stations, set against the backdrop of the Hualapai Mountains"
    ],
    "Arizona Route 66 Museum": [
        "Located in the restored 1907 Powerhouse building in downtown Kingman, tracing Route 66 history decade by decade",
        "Life-size dioramas recreate gas stations, diners, and motels from the 1920s through the 1960s with period artifacts",
        "Interactive exhibits include a 1950s Corvette you can sit in and a recreation of a classic roadside tourist trap",
        "Kingman was a key stop on Route 66 — the museum captures the spirit of the Mother Road's golden age"
    ],
    "Saguaro National Park West": [
        "Dense forest of giant saguaro cacti — some over 200 years old and 40 feet tall — across the Tucson Mountain District",
        "The Bajada Loop Drive winds through a saguaro forest so thick it looks like a cactus city against the mountain backdrop",
        "Signal Hill Petroglyphs trail leads to a cluster of ancient Hohokam rock art atop a desert hill with panoramic views",
        "Saguaros bloom in May-June with white waxy flowers at their tips — Arizona's state flower"
    ],
    "Mount Lemmon Scenic Drive": [
        "27-mile mountain highway climbing 6,000 feet from Tucson's desert floor to a 9,157-foot peak in the Santa Catalinas",
        "The drive transitions through five climate zones — from saguaro desert through oak woodland to subalpine fir forest",
        "Temperatures drop 20-30°F from base to summit; locals joke it's the only place you can go from swimming to skiing in an hour",
        "Summerhaven village near the top has cafes, cabins, and trailheads into the Pusch Ridge Wilderness"
    ],
    "Catalina State Park": [
        "Desert park at the base of the Santa Catalina Mountains with saguaro-studded trails and Romero Canyon waterfalls",
        "The Romero Pools hike follows a riparian canyon to natural rock pools — a desert oasis in the shadow of the mountains",
        "Excellent birdwatching; the park sits on a transition zone between desert and mountain habitats",
        "Dog-friendly trails and a campground with mountain views make it a great base for exploring the Tucson area"
    ],
    "White Sands National Park": [
        "275 square miles of brilliant white gypsum sand dunes — the largest gypsum dune field on Earth",
        "The dunes are cool to the touch even in summer; the white gypsum reflects rather than absorbs heat",
        "Dunes Drive winds 8 miles into the heart of the dune field where sand stretches to the horizon in every direction",
        "Sunset turns the white sand pink, orange, and purple — then the full moon rises and the dunes glow silver"
    ],
    "US-82 Cloudcroft Highway": [
        "Steep mountain highway climbing 4,000 feet from the Tularosa Basin to the Sacramento Mountains in 16 miles",
        "Dramatic hairpin curves with views across the vast white expanse of White Sands and the Tularosa Basin below",
        "The temperature drops 20+ degrees as you climb from desert heat to cool mountain pine forests",
        "One of New Mexico's most scenic drives — the contrast between desert basin and mountain forest is extraordinary"
    ],
    "Osha Trail": [
        "Quiet mountain trail through mixed-conifer forest near Cloudcroft with wildflowers and dappled sunlight",
        "Named for the osha plant, used medicinally by the Apache and Hispanic communities of the Sacramento Mountains",
        "Moderate difficulty with gentle elevation changes; a peaceful contrast to the desert landscapes below",
        "The Sacramento Mountains get more precipitation than anywhere else in southern New Mexico — lush and green"
    ],
    "Dog Canyon Trail": [
        "Trail descending into Dog Canyon on the western slope of the Sacramento Mountains with views across the Tularosa Basin",
        "Part of Oliver Lee Memorial State Park — the canyon is a riparian oasis in the otherwise arid basin",
        "Historical significance as a route used by the Apache, Spanish settlers, and rancher Oliver Lee",
        "Desert bighorn sheep and golden eagles are frequently spotted along the canyon walls"
    ],
    "Rim Trail Cloudcroft": [
        "Scenic rim trail above the village of Cloudcroft with views stretching across the Tularosa Basin to White Sands",
        "The Sacramento Mountains' high elevation (8,600+ feet) keeps temperatures cool even in midsummer",
        "The trail winds through old-growth mixed-conifer forest — a mountain-top ecosystem isolated from surrounding desert",
        "Cloudcroft is one of the highest towns in New Mexico; the Victorian-era lodge and cabins add historic charm"
    ],
    "16 Springs Canyon Campground": [
        "Secluded campground in Lincoln National Forest surrounded by ponderosa pine and mixed-conifer forest",
        "Named for the natural springs that feed the canyon creek — a cool, shaded retreat from the desert below",
        "Basic amenities in a peaceful setting; the sound of the creek and wind in the pines is the main attraction",
        "Excellent base for exploring the Sacramento Mountains' trail system and the nearby historic town of Cloudcroft"
    ],
    "National Solar Observatory at Sunspot": [
        "Active solar research facility at 9,200 feet in the Sacramento Mountains, still studying the sun daily",
        "The visitor center has exhibits on solar physics, and you can view the sun through specialized telescopes",
        "The Apache Point Observatory nearby operates one of the world's premier research telescopes for the Sloan Digital Sky Survey",
        "The drive to Sunspot passes through pristine mountain forest with panoramic views at the summit"
    ],
    "Rio Grande Bosque Trail": [
        "Cottonwood-lined trail along the Rio Grande through Albuquerque's riverside bosque (woodland) — a major urban nature corridor",
        "The bosque ecosystem supports great blue herons, sandhill cranes (in winter), roadrunners, and coyotes",
        "16+ miles of paved and unpaved paths perfect for walking, running, or biking with river access throughout",
        "The fall cottonwood color in late October turns the bosque golden — one of Albuquerque's most beautiful seasons"
    ],
    "Old Town Albuquerque": [
        "Historic Spanish colonial plaza founded in 1706, with adobe buildings surrounding a tree-shaded central square",
        "Over 100 shops, galleries, and restaurants specializing in traditional New Mexican cuisine and Native American art",
        "San Felipe de Neri Church, built in 1793, is one of the oldest surviving structures in Albuquerque",
        "Don't miss the Indian Pueblo Cultural Center nearby — 19 pueblos sharing their living culture"
    ],
    "Santa Fe Plaza": [
        "The historic heart of Santa Fe since 1610 — the oldest public plaza in the US, surrounded by adobe galleries and the Palace of the Governors",
        "Native American artisans sell handmade jewelry, pottery, and textiles under the portal of the Palace of the Governors daily",
        "Canyon Road, a half-mile walk from the plaza, has 100+ art galleries in converted adobe homes — the densest gallery district in the US",
        "The cuisine is uniquely New Mexican: green and red chile, sopaipillas, and blue corn everything"
    ],
    "Las Vegas, NM": [
        "Historic plaza town with over 900 buildings on the National Register — more than any other city in New Mexico",
        "The original town plaza, established in 1835, has beautiful Victorian and Territorial architecture surrounding a central park",
        "Featured as a filming location for No Country for Old Men, Red Dawn, and several other Hollywood productions",
        "Montezuma Castle (now United World College) is a stunning Queen Anne-style hotel built in 1886, worth the short detour"
    ],
    "Raton Pass": [
        "Historic mountain pass at 7,834 feet on the Colorado-New Mexico border — a key gateway on the Santa Fe Trail",
        "The pass was once a toll road operated by Richens 'Uncle Dick' Wootton, who charged pioneers to cross",
        "I-25 follows the same route through the pass; the surrounding mesas and mountains mark the transition between the Great Plains and the Rockies",
        "Nearby Sugarite Canyon State Park has excellent hiking and a gorgeous mountain lake"
    ],
    "Garden of the Gods": [
        "Dramatic red sandstone formations thrust 300+ feet skyward against the backdrop of Pikes Peak — free admission, open year-round",
        "Balanced Rock, Kissing Camels, and Cathedral Spires are formations 300 million years old, tilted vertical by tectonic forces",
        "Paved trails wind between the formations; the Central Garden Trail is wheelchair-accessible with the best up-close views",
        "Sunrise and sunset light up the red rock against blue sky and snow-capped Pikes Peak — Colorado's most photographed landscape"
    ],

    # ═══════════════════ ROUTE 5: The Yellowstone Trail ═══════════════════
    "Donner Memorial State Park": [
        "Memorial to the ill-fated Donner Party of 1846-47, set in a beautiful alpine valley near Donner Lake at 5,900 feet",
        "The Emigrant Trail Museum tells the full story with artifacts recovered from the campsite and the Sierra crossing",
        "The memorial stone's pedestal is 22 feet tall — the depth of the snow that trapped the wagon party",
        "Donner Lake itself is gorgeous for swimming, kayaking, and picnicking in the shadow of granite Sierra peaks"
    ],
    "Truckee, CA (en route)": [
        "Historic railroad and logging town in the Sierra Nevada with a walkable downtown of restaurants, breweries, and boutiques",
        "The brick-and-timber Commercial Row dates to the 1860s — still the town's main drag, now with craft cocktails and farm-to-table dining",
        "Gateway to Tahoe National Forest, Donner Lake, and world-class ski resorts — vibrant year-round",
        "The town has a genuine mountain community feel without the pretension of some neighboring resort towns"
    ],
    "Virginia Lake Park & Off-Leash Dog Park": [
        "Popular urban park in south Reno with a 1.2-mile paved loop around Virginia Lake and a dedicated off-leash dog area",
        "The lake attracts geese, ducks, and pelicans; the surrounding park has picnic areas and playgrounds",
        "A neighborhood gem where locals walk, jog, and let dogs socialize — a welcome stretch break if passing through Reno",
        "The park's mature trees and manicured lawns are a green oasis in the high desert landscape"
    ],
    "Reno Riverwalk District": [
        "Pedestrian promenade along the Truckee River through downtown Reno with restaurants, parks, and public art",
        "Wingfield Park, an island in the middle of the river, hosts summer concerts and festivals",
        "The Riverwalk connects to miles of paved trail along the Truckee River heading west toward Verdi",
        "Reno has reinvented itself from casino town to outdoor recreation hub — the Riverwalk is the centerpiece"
    ],
    "Shoshone Falls": [
        "212-foot waterfall on the Snake River — taller than Niagara Falls and known as the 'Niagara of the West'",
        "The falls are most dramatic in spring (April-June) when snowmelt fills the Snake River to capacity",
        "Viewpoints from both the rim and a lower platform give different perspectives of the horseshoe-shaped cascade",
        "Shoshone Falls Park has picnic areas, swimming access, and a boat ramp; the canyon views alone are worth the stop"
    ],
    "Perrine Bridge & Snake River Canyon": [
        "486-foot-high bridge spanning the Snake River Canyon — one of the few bridges in the US where BASE jumping is legal year-round",
        "The canyon is 500 feet deep here; the bridge deck offers vertigo-inducing views straight down to the river",
        "Evel Knievel attempted to jump the canyon on a rocket-powered 'Skycycle' in 1974 — the launch ramp is still visible",
        "The Centennial Waterfront Park below the bridge offers walking trails along the canyon floor"
    ],
    "Centennial Waterfront Park": [
        "Riverfront park in Twin Falls along the Snake River with walking paths, fishing access, and canyon views",
        "Connected to the Canyon Rim Trail, which offers dramatic views of the Snake River Canyon from the top",
        "A peaceful spot to stretch your legs, walk the dog, and take in the canyon scenery",
        "Twin Falls is the gateway to the Magic Valley — an agricultural region surrounded by volcanic landscape"
    ],
    "Dierkes Lake": [
        "Scenic lake tucked into the rim of the Snake River Canyon near Twin Falls, popular for swimming, fishing, and cliff jumping",
        "The surrounding basalt cliffs create a natural amphitheater; short trails ring the lake and access the canyon rim",
        "A locals' favorite swimming hole in summer — the clear water and cliff scenery feel hidden away",
        "The lake sits just upstream from Shoshone Falls, making it easy to combine both attractions in one stop"
    ],
    "Craters of the Moon National Monument (optional detour)": [
        "Vast lava field covering 618 square miles — an otherworldly landscape of cinder cones, lava tubes, and basalt flows",
        "The 7-mile loop drive passes cinder cones you can climb, tree molds, and entrances to lava tube caves",
        "NASA astronauts trained here in the 1960s because the terrain resembles the lunar surface",
        "The most recent eruptions were only 2,000 years ago; geologists consider this one of the most likely volcanic systems to erupt again"
    ],
    "Idaho Falls River Walk": [
        "Paved trail along the Snake River through downtown Idaho Falls, passing the famous man-made waterfall and LDS temple",
        "The falls are actually a series of diversion dams that create a dramatic cascade across the full width of the river",
        "Riverside parks and Japanese gardens along the 5-mile path make for pleasant walking with views of the Teton Range on clear days",
        "A convenient stop between Twin Falls and Yellowstone — stretch your legs and grab lunch downtown"
    ],
    "Freeman Park Off-Leash Dog Area": [
        "Large off-leash dog area in Idaho Falls with open fields, shade trees, and views of the surrounding mountains",
        "Well-maintained with separate areas for large and small dogs, water stations, and waste bag stations",
        "A welcome stop for dogs who've been cooped up during a long driving day through southern Idaho",
        "Adjacent to the Snake River greenbelt for on-leash walks after some off-leash time"
    ],
    "Tautphaus Park": [
        "Idaho Falls' largest city park featuring the Idaho Falls Zoo, playground, and shaded picnic areas",
        "The zoo houses over 300 animals with a focus on Northern Rockies wildlife — grizzlies, wolves, snow leopards",
        "The park's mature trees and large open spaces make it a pleasant spot for walking and relaxing",
        "Fun stop if you need a break from driving; the zoo is small enough to see in 1-2 hours"
    ],
    "Upper Mesa Falls (en route)": [
        "114-foot waterfall on the Henrys Fork of the Snake River — one of the last major undisturbed waterfalls in the Rockies",
        "A short, wheelchair-accessible boardwalk leads through the forest to a dramatic viewpoint at the falls' brink",
        "Unlike most western waterfalls, Upper Mesa Falls has never been dammed or diverted — it flows in its natural state",
        "The nearby Lower Mesa Falls (65 feet) can be viewed from a separate overlook; both are worth the slight detour"
    ],
    "Rendezvous Ski Trails (Summer Hiking)": [
        "Cross-country ski trail system outside West Yellowstone that transforms into hiking and mountain biking trails in summer",
        "Well-marked loops through lodgepole pine forest with wildflower meadows and occasional wildlife sightings",
        "The trails offer a quieter alternative to the busy Yellowstone roads and trailheads",
        "A good place to spot moose, elk, and sometimes grizzly bears in the early morning or evening"
    ],
    "Grizzly & Wolf Discovery Center": [
        "Wildlife park in West Yellowstone housing grizzly bears and gray wolves that can't be released into the wild",
        "The bears are active and visible year-round — unlike in Yellowstone where sightings aren't guaranteed",
        "Educational programs cover bear safety, wolf ecology, and the history of these species in the Greater Yellowstone Ecosystem",
        "A great complement to Yellowstone — you'll see bears up close and learn how to stay safe in bear country"
    ],
    "Hebgen Lake": [
        "Mountain lake just north of West Yellowstone created by a 1959 earthquake that triggered a massive landslide",
        "The Earthquake Lake Visitor Center tells the story of the 7.3 magnitude quake that killed 28 people and dammed the river",
        "The lake is surrounded by national forest with excellent fishing, kayaking, and wildlife viewing",
        "Osprey, bald eagles, and moose are common along the shoreline; the mountain backdrop is classic Montana"
    ],
    "Old Faithful & Upper Geyser Basin": [
        "The world's most famous geyser erupts 130-180 feet every 44-125 minutes with remarkable predictability",
        "The Upper Geyser Basin has the densest collection of geysers on Earth — over 150 in just one square mile",
        "Boardwalk trails pass Morning Glory Pool (an impossibly blue hot spring), Castle Geyser, and Grand Geyser",
        "Old Faithful Inn, built in 1904, is the world's largest log structure — its lobby alone is worth the visit"
    ],
    "Grand Prismatic Spring (roadside view)": [
        "The largest hot spring in the US (370 feet across) with concentric rings of orange, yellow, green, and deep blue",
        "The vivid rainbow colors come from heat-loving bacteria (thermophiles) that thrive at different temperatures",
        "The Grand Prismatic Overlook trail provides the classic aerial view seen in photographs — it's a short, steep climb",
        "Steam rising from the 160°F water creates an ethereal mist that shifts with the wind, constantly changing the view"
    ],
    "Madison River Valley Wildlife Drive": [
        "The Madison River corridor from Madison Junction to West Yellowstone is one of Yellowstone's prime wildlife viewing areas",
        "Bison herds, elk, and occasionally wolves and grizzly bears can be seen from the road, especially at dawn and dusk",
        "The river is world-class fly fishing water — brown and rainbow trout in clear, cold water against a mountain backdrop",
        "Pull off at any of the riverside turnouts for chances to see wildlife; the valley is especially productive in early morning"
    ],
    "Coffin Lake Trails": [
        "Network of hiking trails near West Yellowstone through lodgepole forest and meadows outside the park boundary",
        "Quieter than Yellowstone's popular trailheads; a chance to hike without the crowds and parking hassles",
        "Wildflowers bloom through the meadows in July; elk and moose frequent the area in early morning",
        "Trail system connects to the Rendezvous Trails for longer loops with varied terrain"
    ],
    "Baker's Hole Campground": [
        "Forest Service campground on the Madison River just north of West Yellowstone, shaded by lodgepole pines",
        "Riverside sites are popular with fly fishermen; the Madison is catch-and-release here with excellent trout fishing",
        "More peaceful and spacious than campgrounds inside Yellowstone, with easy access to the park's west entrance",
        "Bison and elk occasionally wander through camp — a true Yellowstone-area wildlife experience"
    ],
    "Grand Canyon of the Yellowstone (Artist Point)": [
        "The Yellowstone River plunges 308 feet into a 1,000-foot-deep canyon of yellow, orange, and red volcanic rock",
        "Artist Point is the iconic viewpoint — the Lower Falls framed by the golden canyon walls, one of the most painted scenes in the West",
        "The canyon's yellow color comes from hydrothermally altered rhyolite — the 'yellow stone' that named the park",
        "Uncle Tom's Trail descends 300+ steel steps to the base of the falls for a thundering, mist-soaked perspective"
    ],
    "Hayden Valley Wildlife Viewing": [
        "Broad, grassy valley along the Yellowstone River between Canyon Village and Yellowstone Lake — the Serengeti of Yellowstone",
        "Large bison herds, grizzly bears, wolves, coyotes, and trumpeter swans are all regularly spotted here",
        "The valley is too geothermally active for trees, creating open grassland with clear sightlines for wildlife viewing",
        "Bring binoculars or a spotting scope; the early morning and evening hours are prime for predator activity"
    ],
    "Wapiti Valley -- Buffalo Bill Scenic Byway": [
        "52-mile scenic highway through the North Fork of the Shoshone River valley between Yellowstone and Cody, Wyoming",
        "Dramatic volcanic spires, hoodoos, and badlands line the road — Teddy Roosevelt called it 'the most scenic 50 miles in America'",
        "Guest ranches, dude ranches, and fishing lodges dot the valley — authentic Western hospitality country",
        "The Absaroka Range rises on both sides with peaks over 12,000 feet; bighorn sheep are common on the rocky slopes"
    ],
    "Buffalo Bill Center of the West": [
        "Five museums under one roof in Cody, Wyoming — one of the finest museum complexes in the American West",
        "The Whitney Western Art Museum has works by Frederic Remington, Charles M. Russell, and Albert Bierstadt",
        "The Plains Indian Museum presents the history and living cultures of the Crow, Lakota, Cheyenne, and other nations",
        "The Draper Natural History Museum covers the Greater Yellowstone Ecosystem with mounted specimens and interactive exhibits"
    ],
    "Shell Falls": [
        "120-foot waterfall cascading through a narrow granite canyon in the Bighorn Mountains — visible from a paved overlook",
        "The interpretive area explains the geology of the 2.9-billion-year-old Precambrian granite exposed by the canyon",
        "Located right along US-14 (the Bighorn Scenic Byway) — an easy pull-off stop with wheelchair-accessible viewing",
        "The surrounding forest of spruce and fir at 8,000 feet is a cool, green contrast to the plains below"
    ],
    "Bighorn Scenic Byway (US-14 over Big Horns)": [
        "Dramatic mountain highway climbing from the Bighorn Basin over 9,033-foot Granite Pass and descending to Sheridan",
        "The road traverses alpine meadows, granite gorges, and dense evergreen forest with big views in every direction",
        "Medicine Wheel National Historic Landmark near the summit is a mysterious stone circle used by Native peoples for centuries",
        "The descent into Sheridan features sweeping views of the Powder River Basin and the distant Great Plains"
    ],
    "Tongue River Canyon Trail": [
        "Trail following the Tongue River through a limestone canyon in the Bighorn Mountain foothills near Dayton, Wyoming",
        "The canyon walls rise 200+ feet on both sides; the river is popular for swimming holes and fly fishing",
        "A quiet, less-visited canyon with cottonwood shade and chances to see deer, wild turkeys, and raptors",
        "The trail follows an old railroad grade — flat and easy walking through dramatic canyon scenery"
    ],
    "Sheridan Historic Main Street": [
        "Beautifully preserved Western downtown with brick storefronts, the historic Mint Bar, and King's Saddlery",
        "The Mint Bar has been serving cowboys and travelers since 1907 — the original back bar and mounted game trophies remain",
        "King's Saddlery sells handmade saddles and cowboy gear; the attached museum has a remarkable collection of Western artifacts",
        "Sheridan regularly ranks among the best small towns in the West — genuine ranching heritage without tourist kitsch"
    ],
    "Hole in the Wall Country (near Kaycee, WY)": [
        "Remote rangeland country where Butch Cassidy's Wild Bunch hid out in a red-walled canyon between robberies",
        "The actual Hole in the Wall is a gap in a 35-mile-long red sandstone escarpment — accessible only by rough ranch roads",
        "The landscape hasn't changed since the outlaw era; it's still vast, empty, and strikingly beautiful rangeland",
        "The town of Kaycee has a small museum dedicated to the outlaw history and the ranching heritage of the area"
    ],
    "Morad Park Off-Leash Dog Area (Casper)": [
        "Spacious off-leash dog area along the North Platte River in Casper with river access for swimming dogs",
        "The North Platte River Trail connects to miles of paved paths through Casper's park system",
        "Casper Mountain rises to the south, offering scenic contrast to the high-plains downtown",
        "A good midday stop to let dogs run and swim; nearby downtown has breweries and restaurants"
    ],
    "Ayres Natural Bridge Park": [
        "One of only three natural bridges in the US that spans a flowing creek — a 50-foot arch of red sandstone over LaPrele Creek",
        "Free county park with picnic areas, camping, and short trails in a shady canyon setting",
        "The bridge was a landmark on the Oregon Trail; emigrant journals describe camping here in the 1840s-60s",
        "A peaceful, uncrowded stop between Casper and Cheyenne — most travelers don't know it exists"
    ],
    "Casper, WY (lunch stop)": [
        "Central Wyoming's largest city, set on the North Platte River with Casper Mountain providing a dramatic southern backdrop",
        "The National Historic Trails Interpretive Center covers the Oregon, Mormon, California, and Pony Express trails",
        "Downtown has a growing craft brewery scene and locally owned restaurants along a revitalized main street",
        "Fort Caspar Museum reconstructs the military post and telegraph station that gave the city its name"
    ],

    # ═══════════════════ ROUTE 6: Death Valley & Beyond ═══════════════════
    "Trona Pinnacles": [
        "Over 500 tufa towers rising from the dry bed of Searles Lake — some over 140 feet tall, formed underwater 10,000-100,000 years ago",
        "The pinnacles are calcium carbonate formations left behind as the lake evaporated during the last Ice Age",
        "Used as a filming location for Star Trek V, Battlestar Galactica, and Planet of the Apes — genuinely alien landscape",
        "Free BLM site; a dirt road leads to the formations. Best photographed at dawn or dusk when the towers cast long shadows"
    ],
    "Death Valley - Zabriskie Point": [
        "Eroded badlands of golden and cream-colored mudstone forming a surreal landscape of ridges and gullies below Amargosa Range",
        "One of the most photographed spots in Death Valley — the view at sunrise is world-famous, with layers of warm color",
        "The formations are lake sediments from 5 million years ago, uplifted and carved by rain into a miniature mountain range",
        "A short paved path leads to the viewpoint; the Golden Canyon trail below connects for a longer hike through the formations"
    ],
    "Death Valley - Badwater Basin": [
        "The lowest point in North America at 282 feet below sea level — a vast salt flat stretching to the horizon",
        "Walk out onto the geometric salt polygons; the hexagonal patterns formed by evaporation extend for miles",
        "On the cliff above, a small sign marks sea level — the scale is staggering when you look up at it from the basin floor",
        "Telescopic Peak, the highest point in Death Valley (11,049 feet), is visible from Badwater — 11,331 feet of vertical relief in 15 miles"
    ],
    "Wildrose Charcoal Kilns": [
        "Ten beehive-shaped stone kilns built in 1877 to produce charcoal for silver smelting in the Panamint Range",
        "Each kiln is 25 feet tall and perfectly crafted by Swiss stonemasons — they still stand in near-perfect condition",
        "The high-elevation site (6,800 feet) offers panoramic views and cooler temperatures than the valley floor",
        "The kilns have remarkable acoustics — stand inside one and whisper to hear the echo in the dome overhead"
    ],
    "Vermilion Cliffs": [
        "Massive escarpment of red, orange, and purple sandstone stretching 30 miles across the Arizona-Utah border",
        "Home to The Wave, a surreal sandstone formation requiring a lottery permit — one of the most sought-after hikes in the US",
        "The cliffs support a California condor reintroduction program; the endangered birds can sometimes be spotted soaring along the rim",
        "Lees Ferry, at the base of the cliffs, is the put-in point for Colorado River rafting trips through the Grand Canyon"
    ],
    "Navajo Bridge": [
        "Twin steel arch bridges spanning Marble Canyon 470 feet above the Colorado River — the only river crossing for 600 miles",
        "The original 1929 bridge is now a pedestrian walkway; you can look straight down to the emerald-green river below",
        "California condors frequently roost on the bridge structure — look for their numbered wing tags",
        "The bridge connects the Arizona Strip to the rest of the state; Marble Canyon below is the start of the Grand Canyon"
    ],
    "Horseshoe Bend": [
        "The Colorado River makes a dramatic 270-degree bend around a sandstone mesa 1,000 feet below the overlook",
        "One of the most photographed landscapes in the American Southwest — the scale is almost impossible to comprehend",
        "A 1.5-mile round-trip walk from the parking area to the unguarded rim; the final reveal is sudden and breathtaking",
        "Best photographed mid-morning to early afternoon when the sun illuminates the canyon walls and the river glows green"
    ],
    "Lake Powell": [
        "186-mile-long reservoir on the Colorado River with 1,960 miles of shoreline — more than the entire US Pacific coast",
        "Red sandstone canyons filled with turquoise water create a surreal juxtaposition of desert and lake",
        "Houseboating, kayaking, and swimming in side canyons like Antelope Canyon and Labyrinth Canyon are unforgettable",
        "Rainbow Bridge, a 290-foot natural bridge accessible by boat, is one of the world's largest known natural bridges"
    ],
    "Wahweap Campground": [
        "Large campground on the shores of Lake Powell near Page, Arizona with panoramic desert and lake views",
        "Full hookups available; sites near the water's edge have sunset views over the lake and surrounding mesa country",
        "Walking distance to Wahweap Marina for boat rentals, guided tours, and dinner cruises on the lake",
        "The desert setting means incredible stargazing — the dark skies and open horizon are hard to beat"
    ],
    "Glen Canyon Dam": [
        "710-foot-high concrete arch dam that created Lake Powell — one of the tallest dams in the US",
        "The Carl Hayden Visitor Center offers guided tours inside the dam with views from the top and explanations of the engineering",
        "Below the dam, the Colorado River runs clear and cold through Glen Canyon — a dramatic contrast to the red desert above",
        "The dam's construction in the 1960s was one of the most controversial environmental decisions in American history"
    ],
    "Durango Animas River Trail": [
        "Paved riverwalk following the Animas River through historic downtown Durango with mountain views throughout",
        "The trail passes Victorian-era architecture, breweries, and restaurants — easy to combine exercise with exploration",
        "In summer, kayakers and tubers float the river alongside the trail; fly fishermen work the quieter stretches",
        "The Durango & Silverton Narrow Gauge Railroad parallels sections of the trail — watch steam trains pass"
    ],
    "Smelter Mountain Off-Leash": [
        "Off-leash dog area on the flanks of Smelter Mountain above Durango with views across the Animas Valley",
        "The open mesa-top terrain gives dogs room to run with the La Plata Mountains and San Juan Range as backdrop",
        "Short trails connect the off-leash area to viewpoints overlooking downtown Durango and the river below",
        "A locals' favorite for morning and evening dog walks with sunset views that rival any formal overlook"
    ],
    "Wolf Creek Pass": [
        "10,857-foot mountain pass on US-160, one of the snowiest spots in Colorado, with dramatic alpine scenery year-round",
        "The pass crosses the Continental Divide through dense spruce-fir forest and open alpine meadows",
        "Made famous by the C.W. McCall song — the descent to Pagosa Springs has sweeping switchbacks and mountain views",
        "Treasure Falls, a 105-foot waterfall visible from the road, is a quick stop on the east side of the pass"
    ],
    "San Luis Valley": [
        "The largest alpine valley in the world — a vast, flat expanse at 7,500 feet surrounded by 14,000-foot peaks",
        "The valley floor is so flat and dry that the sand dunes at its edge (Great Sand Dunes NP) seem impossible",
        "Sandhill cranes stage here in spring and fall; the Monte Vista National Wildlife Refuge hosts thousands",
        "The oldest continuously inhabited town in Colorado (San Luis, 1851) anchors the valley's Hispanic heritage"
    ],
    "Great Sand Dunes (distant view)": [
        "North America's tallest sand dunes — Star Dune rises 750 feet against the Sangre de Cristo Mountains",
        "The dunes were formed by sand blown from the San Luis Valley floor and trapped against the mountain range",
        "Medano Creek flows along the dune base in late spring, creating a beach-like experience at 8,200 feet elevation",
        "The contrast of golden dunes, green alpine forest, and snow-capped peaks is unlike anything else on the continent"
    ],
    "Fairplay / South Park": [
        "Historic mining town at 9,953 feet, inspiration for the TV show 'South Park' — the real South Park is the valley below",
        "South Park City Museum recreates a 19th-century mining town with 40+ restored buildings and 60,000 artifacts",
        "The actual South Park is a vast mountain grassland (a 'park' in Colorado geography) ringed by mountain ranges",
        "Highway 285 through the valley is one of Colorado's most scenic drives with views of the Mosquito Range"
    ],

    # ═══════════════════ ROUTE 7: The Pacific Northwest Loop ═══════════════════
    "Sacramento": [
        "California's capital city with a walkable Old Sacramento waterfront district featuring Gold Rush-era buildings and wooden boardwalks",
        "The California State Railroad Museum is one of the finest railroad museums in North America with restored locomotives and cars",
        "Farm-to-fork dining capital — the agricultural bounty of the Central Valley is showcased in the city's restaurants",
        "The Tower Bridge, a golden vertical-lift bridge over the Sacramento River, is an art deco landmark lit up at night"
    ],
    "Lake Siskiyou": [
        "Mountain lake at the foot of Mount Shasta with a swimming beach, kayak rentals, and a 7-mile walking trail circling the shore",
        "Mount Shasta (14,179 feet) reflects perfectly in the lake's surface on calm mornings — a photographer's dream",
        "The lake is warm enough for swimming in summer but surrounded by evergreen forest — Pacific Northwest at its best",
        "A peaceful stop between the Sacramento Valley and southern Oregon; the mountain dominates the view from every angle"
    ],
    "Mount Shasta Headwaters": [
        "Natural spring at the base of Mount Shasta where crystal-clear, ice-cold water emerges directly from the mountain's snowpack",
        "The spring is believed by many to have spiritual properties; it's a gathering place for diverse spiritual communities",
        "Located in Mount Shasta City Park, the headwaters feed the Sacramento River — the beginning of California's most important waterway",
        "The water is cold (40°F year-round), pure, and free-flowing — fill your bottles at the source"
    ],
    "Crater Lake National Park": [
        "The deepest lake in the US (1,943 feet) filling a collapsed volcanic caldera — the water is an impossibly deep sapphire blue",
        "Wizard Island, a volcanic cinder cone rising 700 feet from the lake surface, looks like a miniature volcano within a volcano",
        "Rim Drive circles the caldera with 30+ overlooks, each revealing a different perspective of the lake's color and scale",
        "The lake has no inlet or outlet — it's filled entirely by rain and snowmelt, making it one of the clearest bodies of water on Earth"
    ],
    "Pilot Butte": [
        "Volcanic cinder cone in the heart of Bend, Oregon with a paved trail spiraling to a 360-degree summit viewpoint",
        "The top offers views of 10 Cascade volcanoes on a clear day — from Mount Hood to Mount Bachelor",
        "A popular sunrise and sunset hike for locals; the trail is about 1 mile to the top with moderate elevation gain",
        "One of the few cinder cones in the US located entirely within a city — it's basically Bend's backyard volcano"
    ],
    "Deschutes River Trail": [
        "Scenic trail system along the Deschutes River through Bend, Oregon, from downtown to Benham Falls",
        "The river alternates between calm stretches perfect for paddleboarding and Class III-IV whitewater rapids",
        "Sections of the trail pass through old-growth ponderosa pine forest with views of volcanic peaks",
        "In summer, the river is the social center of Bend — tube rentals, swimming holes, and riverside parks everywhere"
    ],
    "Tumalo Falls": [
        "97-foot waterfall cascading over a basalt cliff in the Deschutes National Forest just west of Bend",
        "A short paved walk from the parking area leads to an overlook with the falls framed by evergreen forest",
        "The North Fork Trail continues above the falls past a series of smaller cascades — 6+ falls in 4 miles",
        "One of the most popular hikes near Bend; arrive early for parking in summer"
    ],
    "Crux Fermentation Project": [
        "Craft brewery in Bend, Oregon with a sprawling outdoor patio and views of the Deschutes River and surrounding mountains",
        "Known for experimental sour ales, Belgian-style farmhouse beers, and barrel-aged specialties",
        "The location in a converted AAMCO auto shop has become one of Bend's most iconic gathering places",
        "Dog-friendly patio; pair a tasting flight with a wood-fired pizza from the food truck"
    ],
    "Tumalo State Park Campground": [
        "Popular campground along the Deschutes River just northwest of Bend with sites shaded by ponderosa pines",
        "River access for swimming and wading; the campground's beach area is popular with families in summer",
        "Central location for exploring Bend's brewery scene, mountain biking trails, and high-desert attractions",
        "The park has yurts and cabins for those who prefer not to tent camp; reservations fill early in summer"
    ],
    "Worthy Brewing Observatory": [
        "Craft brewery in Bend with an on-site astronomical observatory — drink beer and stargaze through a serious telescope",
        "The hop garden, on-site farm, and solar panels reflect the brewery's commitment to sustainability",
        "Dog-friendly beer garden with mountain views; their Worthy IPA is a local flagship",
        "One of the most unique brewery experiences in Oregon — where else can you observe Jupiter's moons between pints?"
    ],
    "Shevlin Park": [
        "600-acre forested park along Tumalo Creek just west of Bend with 7+ miles of trails through ponderosa pine forest",
        "The 5-mile loop trail follows the creek through a canyon with old-growth trees and wildflower meadows",
        "Off-leash dog areas in the park make it a favorite for local dog owners; the creek provides natural cooling",
        "Less crowded than Phil's Trail and the more famous Bend-area mountain bike networks"
    ],
    "Painted Hills": [
        "Brilliantly colored clay hills banded in red, gold, black, and ochre — one of the Seven Wonders of Oregon",
        "The colors come from ancient volcanic ash layers deposited 30+ million years ago, each color representing different climate conditions",
        "Short trails wind through the formations; the Painted Hills Overlook and Carroll Rim Trail offer the best panoramic views",
        "Colors are most vivid after rain, when the clay absorbs moisture and the pigments intensify"
    ],
    "John Day Fossil Beds - Sheep Rock Unit": [
        "World-class repository of Cenozoic Era fossils spanning 40 million years of North American plant and animal evolution",
        "The Thomas Condon Paleontology Center displays fossils of ancient horses, saber-toothed cats, and bizarre oreodonts",
        "Blue Basin, a natural amphitheater of blue-green volcanic ash, has a trail with bronze casts of fossils found in the rock",
        "The dramatic landscape of layered volcanic ash and basalt tells the story of Oregon's explosive volcanic past"
    ],
    "Kam Wah Chung State Heritage Site": [
        "Remarkably preserved 1860s Chinese apothecary and general store in John Day, Oregon — a time capsule of frontier Chinese life",
        "The building was sealed for decades; when reopened, it contained thousands of herbs, teas, and traditional medicines",
        "Tells the often-overlooked story of Chinese immigrants who played a vital role in Oregon's mining and railroad history",
        "Free guided tours explain the medicinal practices, social dynamics, and cultural preservation of the Chinese community"
    ],
    "Blue Mountain Scenic Byway": [
        "Scenic highway through the Blue Mountains of eastern Oregon, crossing forested mountain passes and descending into river valleys",
        "The route passes through Malheur and Ochoco National Forests with views of the Strawberry Mountain Wilderness",
        "Less traveled than Oregon's coastal and Cascade routes — genuine backcountry forest scenery with minimal traffic",
        "Wildlife viewing opportunities include elk, mule deer, wild turkeys, and black bears in the mountain forests"
    ],
    "Boise River Greenbelt": [
        "25-mile paved path following the Boise River through the city — one of the best urban trail systems in the West",
        "River access for floating, fishing, and wading; in summer, Boiseans float the river on inner tubes by the thousands",
        "The greenbelt connects major parks, the Boise State campus, and downtown's restaurant and brewery district",
        "Mature cottonwood trees shade the path; the foothills above the city turn green in spring and golden in fall"
    ],
    "Freak Alley Gallery": [
        "The largest outdoor gallery in the Pacific Northwest — a downtown Boise alley covered floor-to-ceiling in murals and street art",
        "Local and visiting artists repaint and add new works regularly, so the gallery is always evolving",
        "The murals range from photorealistic portraits to abstract explosions of color to social commentary",
        "Free and always open; a 5-minute walk from Boise's main downtown drag — don't miss the pieces on the rooftops"
    ],
    "Hemingway Memorial": [
        "Simple stone memorial to Ernest Hemingway in a grove of aspens and cottonwoods along Trail Creek in Ketchum, Idaho",
        "Hemingway chose Sun Valley as his home and wrote parts of 'For Whom the Bell Tolls' here — he is buried in the Ketchum cemetery",
        "The memorial overlooks the creek and surrounding mountains — a contemplative spot that captures why Hemingway loved this place",
        "Sun Valley and Ketchum remain an active outdoor community with skiing, fishing, hiking, and a vibrant arts scene"
    ],
    "Draper Preserve": [
        "Nature preserve along the Big Wood River in Hailey, Idaho with wetlands, cottonwood groves, and mountain views",
        "Walking trails loop through riparian habitat with excellent birdwatching — great blue herons, kingfishers, and hawks",
        "A quiet alternative to the busier trails in Sun Valley and Ketchum; the river setting is peaceful and photogenic",
        "The Wood River Trail, a paved path running the length of the valley, passes directly through the preserve"
    ],
    "Galena Summit Overlook": [
        "8,701-foot mountain pass on Highway 75 with a sweeping view of the Sawtooth Valley and the jagged Sawtooth Range",
        "The overlook is one of the most iconic viewpoints in Idaho — the serrated granite peaks stretch across the horizon",
        "The descent from the summit into the Sawtooth Valley is one of the most dramatic drives in the Northern Rockies",
        "Stanley, the small town at the bottom of the valley, is surrounded by more wilderness than almost any other place in the Lower 48"
    ],
    "Sawtooth Brewery": [
        "Craft brewery in the tiny mountain town of Stanley, Idaho (population 63) with Sawtooth Range views from the patio",
        "Stanley sits at the confluence of the Salmon River and Valley Creek, surrounded by the Sawtooth Wilderness",
        "Cold beer after a day of hot springs, hiking, or fishing in one of America's most remote small towns",
        "The brewery is a gathering spot for the local ranching and recreation community — genuine mountain-town atmosphere"
    ],
    "Craters of the Moon": [
        "Vast basaltic lava field covering 618 square miles — an otherworldly landscape of cinder cones, lava tubes, and volcanic flows",
        "The 7-mile loop drive passes cinder cones you can climb, tree molds, and entrances to lava tube caves you can explore",
        "NASA astronauts trained here in the 1960s because the terrain closely resembles the actual lunar surface",
        "Most recent eruptions were only 2,000 years ago; this remains one of the most active volcanic rift zones in North America"
    ],
    "Grand Teton NP - Mormon Row": [
        "Historic homestead district with photogenic barns and cabins framed by the jagged Teton Range — one of the most photographed scenes in the West",
        "The Moulton Barn is the iconic shot — a weathered wooden barn with the Grand Teton rising directly behind it",
        "Mormon settlers established this farming community in the 1890s; several original structures remain standing",
        "Best photographed at sunrise when the eastern light illuminates the Tetons in warm tones behind the dark barn silhouettes"
    ],
    "Cache Creek Trail System": [
        "Trail network in the hills above Jackson, Wyoming with loops ranging from easy to challenging through sagebrush and aspen groves",
        "Popular with local dog walkers, trail runners, and mountain bikers — a quick escape from Jackson's bustling town square",
        "Wildlife encounters are common — elk, mule deer, and moose use the canyon regularly; bear spray is recommended",
        "The trails climb into the Gros Ventre Range with views down to Jackson Hole and across to the Tetons"
    ],
    "Togwotee Pass": [
        "9,658-foot pass on US-26/287 between Jackson Hole and Dubois with one of the most dramatic mountain vistas in Wyoming",
        "The Absaroka Range, Teton Range, and Wind River Range are all visible from the pass — triple mountain views",
        "The pass area is popular for cross-country skiing and snowmobiling in winter; summer brings wildflower meadows",
        "The descent toward Dubois enters the badlands of the Wind River Valley — a sudden shift from alpine to desert landscape"
    ],
    "Dubois, WY": [
        "Small Western town in the Wind River Valley known for its large free-roaming bighorn sheep herd visible from town",
        "The National Bighorn Sheep Interpretive Center celebrates the town's resident herd with exhibits and guided viewing tours",
        "Surrounded by the Absaroka and Wind River ranges; the town is a gateway to the Shoshone National Forest",
        "A genuine ranching and outfitting town without tourist veneer — log buildings, Western shops, and welcoming locals"
    ],
    "Elk Mountain & Medicine Bow": [
        "Prominent 11,156-foot peak visible from I-80 and the surrounding Medicine Bow Mountains and National Forest",
        "The region is known for extreme winds — the I-80 corridor near Elk Mountain is one of the windiest stretches of highway in the US",
        "Medicine Bow National Forest offers remote hiking, fishing, and camping with surprisingly few visitors",
        "Owen Wister set 'The Virginian' (1902), the first true Western novel, in the town of Medicine Bow nearby"
    ],
    "Cheyenne": [
        "Wyoming's capital city and historic railroad town, known for Cheyenne Frontier Days — the world's largest outdoor rodeo",
        "The State Capitol building, modeled after the US Capitol, has a gold-leaf dome and houses Wyoming's legislature",
        "Historic downtown features restored Union Pacific Depot, the Cheyenne Botanic Gardens, and the Frontier Days Old West Museum",
        "A genuine Western city where cowboys in working boots share the sidewalks with state legislators"
    ],

    # ═══════════════════ ROUTE 8: Eastern Sierra Scenic ═══════════════════
    "Pinnacles National Park (West Entrance)": [
        "Dramatic volcanic spires and crags rising from the chaparral — remnants of a volcano that erupted 23 million years ago",
        "The West Entrance provides access to the Juniper Canyon Trail and Balconies Cave — a walk-through talus cave with flashlight sections",
        "One of the few places to see the endangered California condor in the wild — up to 40 birds soar among the pinnacles",
        "Rock climbing is world-class here; the volcanic breccia formations create hundreds of established climbing routes"
    ],
    "Sequoia Gateway": [
        "The town of Three Rivers serves as the gateway to Sequoia National Park, nestled along the Kaweah River in the Sierra foothills",
        "The Kaweah River provides swimming holes, kayaking, and scenic picnicking beneath granite boulders and oak trees",
        "Small-town restaurants, lodges, and artists' studios line the winding road — the last services before the park",
        "The surrounding foothills are carpeted in wildflowers in spring; the summer heat sends visitors uphill to the cooler park"
    ],
    "Mobius Arch Trail": [
        "Short loop trail through the Alabama Hills to the famous Mobius Arch, which frames Mount Whitney in its opening",
        "The trail weaves through a maze of weathered granite boulders that look like melted sculptures",
        "Best at dawn when the first light illuminates Mount Whitney through the arch — a classic Eastern Sierra photograph",
        "The Alabama Hills have been used as a filming location for over 400 movies, TV shows, and commercials"
    ],
    "Movie Road": [
        "Unpaved road through the heart of the Alabama Hills, passing rock formations used in countless Hollywood westerns and sci-fi films",
        "Formations along the road are named for films shot there — from Gunga Din (1939) to Iron Man (2008)",
        "The contrast between the rounded granite boulders and the jagged Sierra crest behind is striking and surreal",
        "Free to drive; interpretive signs identify filming locations for classics like Lone Ranger, Tremors, and Django Unchained"
    ],
    "Whitney Portal Road": [
        "Winding mountain road climbing 3,000 feet from Lone Pine to Whitney Portal at the base of Mount Whitney",
        "The Eastern Sierra escarpment rises almost vertically from the valley floor — one of the most dramatic mountain fronts in the world",
        "Whitney Portal has a camp store, restaurant, and the trailhead for the highest peak in the contiguous US (14,505 feet)",
        "Even if you don't hike Whitney, the drive delivers big alpine scenery, a waterfall, and cool mountain air"
    ],
    "Manzanar National Historic Site": [
        "Preserved site of the Japanese American internment camp where 10,000 people were unjustly imprisoned during WWII",
        "The interpretive center has powerful exhibits including personal stories, photographs, and artifacts from the camp",
        "Reconstructed barracks, a mess hall, and the guard tower stand against the backdrop of the Sierra Nevada",
        "A sobering and essential stop — understanding this history is important for every American"
    ],
    "Erick Schat's Bakkery Bishop": [
        "Legendary Eastern Sierra bakery famous for its sheepherder bread — a dense, crusty sourdough loaf baked since 1938",
        "Lines out the door are common; the bakery also makes pastries, sandwiches, and cookies for the road",
        "A mandatory stop in Bishop — it's been fueling hikers, climbers, and road-trippers for nearly a century",
        "The shop is filled with the aroma of fresh bread; grab a loaf of sheepherder bread and a cookie for the drive"
    ],
    "Ancient Bristlecone Pine Forest": [
        "Home to the oldest known living trees on Earth — some bristlecone pines here are over 4,800 years old",
        "The Schulman Grove at 10,000 feet has a self-guided trail through a forest of gnarled, twisted trees that predate the pyramids",
        "Methuselah, the oldest tree (4,856 years), is in the grove but deliberately unmarked to protect it from vandalism",
        "The trees survive in hostile conditions — high altitude, thin soil, and fierce winds — thriving where nothing else can"
    ],
    "Wild Willy's Hot Spring": [
        "Natural hot spring in a meadow near Mammoth Lakes with views of the Sierra crest and Glass Mountains",
        "A boardwalk leads across the meadow to a series of pools at different temperatures — bring your own soaking gear",
        "The setting is idyllic — volcanic hot water surrounded by grassy wetlands with snowy peaks on the horizon",
        "Free and accessible; the spring is a local favorite for post-hike soaking at any time of year"
    ],
    "Convict Lake": [
        "Glacial lake surrounded by dramatic peaks and colorful metamorphic rock in the Eastern Sierra near Mammoth Lakes",
        "Named for an 1871 prison escape and shootout; the colorful canyon walls tell a geological story spanning 400 million years",
        "A 2.5-mile trail loops the lake with fishing access; the still water reflects the peaks perfectly on calm mornings",
        "The resort has a highly rated restaurant — fine dining with a mountain lake setting that rivals any in the Sierra"
    ],
    "Mammoth Mountain Scenic Gondola": [
        "Gondola ride to 11,053-foot summit with 360-degree views of the Sierra Nevada, Owens Valley, and volcanic craters",
        "The Minaret Vista at the top reveals the jagged Minarets, Banner Peak, and the Ritter Range — spectacular alpine scenery",
        "In summer the mountain has hiking and mountain biking trails accessed from the gondola; the summit cafe has the highest espresso in the Sierra",
        "Mammoth is a volcanic system — the gondola passes over fumaroles and volcanic features on the mountainside"
    ],
    "Horseshoe Lake Dog Beach": [
        "Small volcanic lake near Mammoth with a sandy beach area where dogs can swim and play off-leash",
        "CO2 gas from underground volcanic activity has killed trees around portions of the lake — a visible reminder that Mammoth is a volcano",
        "The lake is set in a forest of red fir and lodgepole pine at 8,900 feet — cool and pleasant in summer",
        "A local favorite for dog owners; the sandy beach and calm water are perfect for water-loving dogs"
    ],
    "June Lake Loop": [
        "16-mile scenic loop through the Eastern Sierra passing four alpine lakes, each with its own character and color",
        "June Lake, Gull Lake, Silver Lake, and Grant Lake are each surrounded by granite peaks and aspen groves",
        "Fall color along the loop (usually mid-October) rivals New England — the aspens turn brilliant gold against granite and blue water",
        "The loop road (Highway 158) is one of the most scenic short drives in California"
    ],
    "Twin Lakes Campground": [
        "Campground on the shore of Twin Lakes near Bridgeport, surrounded by towering granite peaks and aspen forest",
        "The lakes are at 7,000 feet with excellent trout fishing and calm water for kayaking and canoeing",
        "The surrounding Hoover Wilderness and Sawtooth Ridge provide dramatic mountain scenery in every direction",
        "Fall camping here is spectacular — the shoreline aspens blaze gold while the peaks are dusted with early snow"
    ],
    "Lakes Basin Drive": [
        "Scenic road through the Eastern Sierra passing multiple alpine lakes with views of volcanic peaks and granite formations",
        "Each lake along the route has its own personality — some for fishing, some for swimming, some for pure scenic beauty",
        "The Eastern Sierra is one of the most dramatic mountain fronts in the world — this drive showcases it beautifully",
        "Wildflowers in summer and golden aspens in fall add seasonal color to the granite and volcanic landscape"
    ],
    "Mono Lake South Tufa": [
        "Otherworldly tufa towers (calcium carbonate formations) rising from the alkaline waters of ancient Mono Lake",
        "The South Tufa area has the most accessible and photogenic formations — some towers are 30 feet tall",
        "Mono Lake is 760,000 years old with no outlet — it's 2.5 times saltier than the ocean and supports brine shrimp and alkali flies",
        "Best at sunset or sunrise when the tufa towers cast long shadows and the Sierra crest glows behind the lake"
    ],
    "Tonopah Stargazing": [
        "Tonopah's extreme remoteness — 100+ miles from any city — makes it one of the darkest places in the contiguous US",
        "The Milky Way is so bright here it casts visible shadows; on a clear night 7,000+ stars are visible to the naked eye",
        "The dedicated stargazing park has telescope pads, red-light-only zones, and informational panels about the night sky",
        "Mining town ambiance by day transforms into a cosmic amphitheater by night — an unforgettable experience"
    ],
    "Nevada Northern Railway": [
        "Operating heritage railroad in Ely, Nevada using original equipment from 1906 — a living, working museum of railroad history",
        "Ride behind a century-old steam locomotive on the same tracks that once hauled copper ore from the mines",
        "The entire railroad complex — shops, depot, roundhouse, and equipment — is a National Historic Landmark",
        "One of the most authentic railroad experiences in the US; some events let you ride in the locomotive cab"
    ],
    "Cave Lake State Park": [
        "Mountain lake at 7,300 feet in the Schell Creek Range near Ely, Nevada — a cool oasis in the Great Basin desert",
        "Trout fishing, kayaking, and swimming in clear mountain water surrounded by pine and juniper forest",
        "A surprisingly lush setting in the middle of Nevada's high desert; the park has camping and day-use areas",
        "Success Summit on the approach road offers panoramic views of the Steptoe Valley and surrounding ranges"
    ],
    "Ward Charcoal Ovens": [
        "Six beehive-shaped stone ovens, 30 feet tall, built in 1876 to produce charcoal for the nearby silver smelters",
        "The ovens are remarkably well-preserved and photogenic — standing in a row against the Nevada mountain backdrop",
        "After the mines closed, the ovens reportedly served as shelter for travelers, outlaws, and stockmen",
        "A state historic park with picnic areas; the surrounding area has excellent dark-sky viewing"
    ],
    "Great Basin NP (distant view)": [
        "Great Basin National Park protects Wheeler Peak (13,063 feet), Lehman Caves, and ancient bristlecone pine groves",
        "The park is one of the least-visited in the system despite having world-class caves, alpine scenery, and dark skies",
        "Wheeler Peak Scenic Drive climbs to 10,000 feet with views spanning 100+ miles across the Basin and Range landscape",
        "Lehman Caves has spectacular formations including rare shield formations found in only a few caves worldwide"
    ],
    "San Rafael Swell": [
        "Massive geologic uplift in central Utah with slot canyons, natural bridges, and colorful sandstone formations",
        "The Wedge Overlook ('Little Grand Canyon') offers views of a 1,200-foot-deep gorge carved by the San Rafael River",
        "Goblin Valley, Temple Mountain, and the Black Dragon Wash pictographs are all part of this rugged region",
        "Largely undeveloped BLM land — the solitude and raw landscape feel like the Utah that existed before the parks were discovered"
    ],
    "Glenwood Springs": [
        "Mountain town at the confluence of the Colorado and Roaring Fork rivers, famous for the world's largest hot springs pool",
        "The Glenwood Hot Springs Pool is 405 feet long, fed by the Yampah hot spring at 122°F",
        "Iron Mountain Hot Springs offers 16 individual soaking pools terraced along the Colorado River",
        "Doc Holliday spent his final years here, seeking relief in the mineral waters; he's buried in the Linwood Cemetery above town"
    ],

    # ═══════════════════ ROUTE 9: Coastal & I-40 Corridor ═══════════════════
    "Pinnacles National Park": [
        "Remnants of a 23-million-year-old volcano split by the San Andreas Fault — half is here, the other half is 195 miles southeast",
        "The High Peaks Trail winds through dramatic volcanic spires with views of the Salinas Valley and distant Monterey Bay",
        "Talus caves formed by fallen boulders create walk-through cave experiences — bring a flashlight for Bear Gulch Cave",
        "One of the best places in California to see endangered California condors soaring above the crags"
    ],
    "San Luis Obispo Downtown": [
        "Charming college town (Cal Poly) with a walkable downtown of restaurants, breweries, and the famous Bubblegum Alley",
        "Thursday Night Farmers' Market transforms Higuera Street into a 6-block festival with live music and local food vendors",
        "Mission San Luis Obispo de Tolosa, founded in 1772, anchors the downtown with its distinctive red-tile roof",
        "The SLO life — laid-back Central Coast culture halfway between LA and San Francisco"
    ],
    "Morro Rock": [
        "576-foot volcanic plug at the mouth of Morro Bay — a sacred Salinan and Chumash site and iconic Central Coast landmark",
        "One of the Nine Sisters, a chain of volcanic peaks stretching between San Luis Obispo and Morro Bay",
        "The rock is a peregrine falcon nesting site and protected ecological reserve; the harbor around it teems with sea life",
        "Best viewed from the Embarcadero or the nearby state park campground with its eucalyptus-shaded sites"
    ],
    "Route 66 Mother Road Museum": [
        "Museum in the historic Harvey House/Casa del Desierto in Barstow celebrating Route 66 history and culture",
        "The building itself is a stunning 1911 railroad hotel designed in a mix of Spanish Renaissance and Classical Revival styles",
        "Exhibits cover the route from Chicago to Santa Monica with vintage photographs, memorabilia, and a reconstructed gas station",
        "Barstow sits at the junction of I-15 and I-40 — a natural crossroads just as it was in the Route 66 era"
    ],
    "Calico Ghost Town": [
        "Restored 1880s silver mining town in the Mojave Desert with original buildings, mine tours, and Old West reenactments",
        "At its peak, Calico had 500 mines producing $86 million in silver ore; today 5 original buildings remain among reconstructions",
        "The Maggie Mine offers a self-guided underground tour through original mining tunnels and shafts",
        "Walter Knott (of Knott's Berry Farm fame) began restoring Calico in the 1950s; it's now a San Bernardino County park"
    ],
    "Snow Cap Drive-In Seligman": [
        "Quirky Route 66 roadside attraction known for its joke-playing owner and Christmas-decorated hot dog stand since 1953",
        "The late Juan Delgadillo decorated every surface with hubcaps, bumper stickers, and kitsch — it's a folk art installation",
        "Famous for practical jokes — ask for a glass of water and get squirted; the mustard dispenser might spray you",
        "Seligman is considered the birthplace of the Route 66 preservation movement — the inspiration for the movie 'Cars'"
    ],
    "Route 66 Seligman": [
        "Small Arizona town that launched the Route 66 preservation movement when barber Angel Delgadillo fought to save the road in 1987",
        "The main drag is lined with vintage motels, diners, and gift shops frozen in 1950s-60s Americana",
        "The town was the inspiration for 'Radiator Springs' in Pixar's Cars — you can see the resemblance everywhere",
        "Angel Delgadillo's barbershop and visitor center is still operating; he's signed thousands of Route 66 maps and postcards"
    ],
    "Flagstaff Historic Downtown": [
        "Northern Arizona's mountain town at 7,000 feet with a walkable historic district of Route 66 motels, breweries, and bookshops",
        "Weatherford Hotel (1900) and Monte Vista Hotel (1927) are downtown landmarks; both are still open with lively bars",
        "The Museum Club ('The Zoo') is a legendary Route 66 honky-tonk roadhouse built inside a log cabin since 1931",
        "Gateway to the Grand Canyon, Sunset Crater, and Sedona — plus the largest ponderosa pine forest in the world"
    ],
    "Sunset Crater Lava Flow Trail": [
        "Trail across a 1,000-year-old lava flow at the base of Sunset Crater, the youngest volcano on the Colorado Plateau",
        "The eruption around 1085 AD was witnessed by the Sinagua people — it buried fields but created fertile volcanic soil",
        "The lava flow trail crosses blocky basalt with interpretive signs explaining the volcanic features and plant recolonization",
        "The crater's rim is tinted red and orange from iron and sulfur oxidation — giving it the 'sunset' color"
    ],
    "Bonito Campground": [
        "Forest Service campground at the base of Sunset Crater in the Coconino National Forest, shaded by ponderosa pines",
        "The campground sits on ancient volcanic cinders; the dark soil and surrounding lava flows create a unique atmosphere",
        "Close to Sunset Crater, Wupatki National Monument, and the Painted Desert — a perfect base camp",
        "Clear, dark skies make this an excellent spot for stargazing in the ponderosa forest"
    ],
    "Walnut Canyon National Monument": [
        "Over 80 cliff dwellings built by the Sinagua people into limestone ledges above a forested canyon near Flagstaff",
        "The Island Trail descends 185 feet (240 steps) into the canyon, passing 25 cliff rooms tucked under overhangs",
        "The Sinagua lived here from about 1125 to 1250 AD, building homes in the south-facing alcoves for warmth and protection",
        "The canyon's ecosystem transitions from ponderosa pine on the rim to walnut and Douglas fir in the cool depths below"
    ],
    "Fatman's Loop Trail": [
        "2.25-mile loop trail in Flagstaff that squeezes through a narrow rock passage — the 'fatman's' squeeze adds adventure",
        "The trail climbs through basalt formations with views of the San Francisco Peaks, Flagstaff, and the surrounding forest",
        "Popular with locals for morning hikes and trail running; the volcanic rock formations are unique",
        "The narrow passage that gives the trail its name is fun to navigate — a minor scramble adds character"
    ],
    "Lake Mary": [
        "Mountain lakes south of Flagstaff surrounded by ponderosa pine forest at 7,000 feet — popular for fishing and picnicking",
        "Upper and Lower Lake Mary provide calm water for fishing (rainbow trout and catfish) and non-motorized boating",
        "The Lake Mary Road is a scenic drive through the Coconino National Forest with several pulloffs and campgrounds",
        "Elk and pronghorn antelope are frequently spotted in the meadows along the road"
    ],
    "Meteor Crater": [
        "The best-preserved meteorite impact crater on Earth — 4,000 feet wide and 570 feet deep, formed 50,000 years ago",
        "The visitor center has interactive exhibits, a genuine 1,406-pound meteorite fragment, and an Apollo space capsule",
        "NASA trained astronauts here for the Moon missions; the crater's lunar-like landscape was perfect practice",
        "The viewing platform at the rim lets you see the full scale — a Boeing 747 could be hidden inside with room to spare"
    ],
    "Route 66 Neon Arch Grants": [
        "Neon arch spanning Route 66 in downtown Grants, New Mexico — a classic Mother Road photo opportunity",
        "Grants was a uranium mining boomtown in the 1950s; the New Mexico Mining Museum has the world's only underground uranium mine tour",
        "The town sits at the foot of Mount Taylor (11,301 feet), sacred to the Navajo as one of their four sacred mountains",
        "A small, authentic Route 66 town that hasn't been over-restored or turned into a tourist trap"
    ],
    "Canyon Road Santa Fe": [
        "Half-mile stretch in Santa Fe with 100+ art galleries, studios, and sculpture gardens in converted adobe homes",
        "The road has been an arts center since the 1920s — it's the densest gallery district in the US",
        "Styles range from traditional Southwestern and Native American art to contemporary, abstract, and avant-garde",
        "Christmas Eve features thousands of farolitos (candle-lit paper bags) lining the road — a magical Santa Fe tradition"
    ],
    "Frank Ortiz Dog Park": [
        "135-acre off-leash dog park in the hills above Santa Fe with trails winding through piñon-juniper woodland",
        "Views of the Sangre de Cristo and Jemez mountains from the park's ridgeline trails",
        "Multiple loops and terrain types — from open meadows to wooded hillsides with plenty of room to roam",
        "One of the largest and most scenic dog parks in New Mexico"
    ],
    "Spanish Peaks": [
        "Twin volcanic peaks (West Spanish Peak 13,626 feet, East Spanish Peak 12,683 feet) rising dramatically above the plains",
        "The Great Dikes radiating from the peaks are massive stone walls up to 100 feet tall, formed by ancient magma intrusions",
        "Visible for 100+ miles across the Great Plains; they served as landmarks for the Santa Fe Trail",
        "The Highway of Legends (CO-12) passes through the area with interpretive pulloffs and spectacular views"
    ],
    "Cherry Creek State Park": [
        "4,000-acre park in the Denver metro area with a reservoir, trails, shooting range, and off-leash dog area",
        "The off-leash dog area covers 107 acres — one of the largest urban off-leash parks in Colorado",
        "The reservoir offers swimming, sailing, and paddleboarding with the Denver skyline and Rocky Mountain views",
        "A welcome green space to decompress if arriving in Denver after days of driving"
    ],
    "Palmer Park": [
        "730-acre park in Colorado Springs with mesa-top trails, red rock formations, and views of Pikes Peak and the Front Range",
        "Dog-friendly trails wind through scrub oak and pine with overlooks of the city, Garden of the Gods, and the plains beyond",
        "The park sits on a mesa above the city — the elevation gives panoramic views without the tourist crowds of Garden of the Gods",
        "Mountain biking and trail running are popular; the network of trails covers terrain from gentle to technical"
    ],

    # ═══════════════════ ROUTE 10: Montana Big Sky ═══════════════════
    "Bidwell Park -- Upper Park": [
        "Wild, undeveloped upper section of Chico's Bidwell Park with swimming holes in Big Chico Creek and rugged hiking trails",
        "Bear Hole and Salmon Hole are popular swimming spots where the creek flows through volcanic rock formations",
        "One of the largest municipal parks in the US at 3,670 acres — the upper park feels like wilderness within city limits",
        "The terrain is oak woodland, basalt formations, and creek canyons — very different from the manicured lower park"
    ],
    "Bidwell Park -- Lower Park & One-Mile Recreation Area": [
        "Shaded, park-like section of Bidwell Park with paved paths, picnic areas, and One-Mile pool in Big Chico Creek",
        "The park's sycamore and oak canopy creates a cool corridor through the Sacramento Valley heat",
        "One-Mile Recreation Area is a free swimming area in the creek — a Chico summertime institution",
        "Scenes from Robin Hood: Prince of Thieves (1991) and The Adventures of Robin Hood (1938) were filmed here"
    ],
    "Sierra Nevada Brewing Company": [
        "Pioneering craft brewery in Chico that helped launch the American craft beer revolution in 1980",
        "Tours include the brewhouse, hop-back room, and barrel-aging cellars; the beer garden is one of the best in California",
        "The Taproom & Restaurant serves farm-to-table food grown on the brewery's own estate garden",
        "Sierra Nevada Pale Ale is one of the most influential American beers ever brewed — taste it at the source"
    ],
    "Downtown Chico": [
        "Walkable college town downtown (Cal State Chico) with a lively mix of restaurants, bars, bookshops, and the historic Senator Theatre",
        "The Thursday Night Market in summer fills several blocks with food vendors, live music, and craft stalls",
        "A friendly, unpretentious town that punches above its weight in dining and nightlife thanks to the university",
        "Bidwell Mansion State Historic Park, the 26-room Victorian home of Chico's founder, is worth a tour"
    ],
    "Feather River Canyon (en route)": [
        "Highway 70 follows the Feather River through a spectacular canyon with tunnels carved through granite walls",
        "The Western Pacific Railroad (now Union Pacific) runs alongside — watch freight trains snake through the canyon",
        "The canyon transitions from oak-studded foothills to evergreen forest as you gain elevation toward the Sierra crest",
        "Often overlooked in favor of I-80, this canyon route is one of California's most scenic mountain drives"
    ],
    "Winnemucca Sand Dunes": [
        "Large sand dune field northeast of Winnemucca, Nevada — a surprising desert playground in the Great Basin",
        "Open for OHV riding, sandboarding, and exploring; the dunes rise up to 60 feet from the desert floor",
        "The setting against the Sonoma Range is photogenic, especially at sunset when the dunes glow orange",
        "Free BLM land with no facilities — pack water and supplies for a raw desert experience"
    ],
    "Martin Hotel -- Basque Dining": [
        "Historic hotel in Winnemucca serving traditional Basque family-style dinners since 1898",
        "The communal dining experience includes soup, salad, bread, beans, french fries, and your choice of meat — all served family-style",
        "Basque sheepherders settled in this part of Nevada in the late 1800s; the Martin Hotel preserves their culinary traditions",
        "A genuinely unique American dining experience — the portions are enormous and the atmosphere is convivial"
    ],
    "Humboldt River Walk": [
        "Walking path along the Humboldt River through Winnemucca with shade trees and benches",
        "The Humboldt was the lifeline of the California Trail — pioneers followed it across the Great Basin",
        "A pleasant stretch break in a town that still feels like a frontier outpost on the transcontinental route",
        "The river is one of the few waterways in the Great Basin; everything around it is desert"
    ],
    "Shoshone Falls (en route, Twin Falls)": [
        "212-foot waterfall on the Snake River — higher than Niagara Falls and known as the 'Niagara of the West'",
        "Spring snowmelt (April-June) produces the most dramatic flows; by late summer, irrigation diversions reduce the cascade",
        "Multiple viewpoints from the rim and lower platforms offer different perspectives of the horseshoe-shaped falls",
        "The surrounding canyon is 500 feet deep with basalt cliffs and desert scrub — dramatic volcanic landscape"
    ],
    "Camel's Back Park & Ridge to Rivers Trails": [
        "Hillside park in Boise's North End with a distinctive camel-hump ridge and access to the Ridge to Rivers trail system",
        "The trails climb from the park into the Boise Foothills with views of the city, Boise River, and Owyhee Mountains",
        "Popular with dog walkers, trail runners, and mountain bikers; the off-leash area is a neighborhood social hub",
        "The foothills turn green in spring, gold in summer, and are snow-dusted in winter — always scenic"
    ],
    "Traveler's Rest State Park": [
        "Historic campsite where the Lewis & Clark expedition rested in September 1805 and June-July 1806",
        "Archaeological evidence confirms this as one of the few verified Lewis & Clark campsites — artifacts were found in situ",
        "The park sits at the confluence of Lolo Creek and the Bitterroot River in a beautiful mountain valley setting",
        "Interpretive trails explain the expedition's journey and the Salish people who lived here for thousands of years"
    ],
    "Rattlesnake National Recreation Area": [
        "25,000-acre wilderness-adjacent recreation area just north of downtown Missoula with hiking, biking, and swimming",
        "Rattlesnake Creek provides swimming holes and fishing; the trail follows the creek into increasingly wild terrain",
        "Despite the name, rattlesnakes are rare here; the area is named for the creek, not the reptiles",
        "One of Missoula's most popular outdoor areas — mountain wilderness is literally a 10-minute drive from downtown"
    ],
    "Mount Sentinel 'M' Trail": [
        "Steep zigzag trail climbing to the concrete 'M' on the hillside above the University of Montana campus",
        "The 'M' viewpoint offers sweeping views of the Missoula Valley, Clark Fork River, and surrounding mountain ranges",
        "A Missoula rite of passage — students, locals, and visitors all make the 2,000-foot climb regularly",
        "The trail continues beyond the M to the summit with increasingly expansive mountain panoramas"
    ],
    "Carousel for Missoula & Caras Park": [
        "Hand-carved carousel in downtown Missoula built entirely by community volunteers over a 4-year period",
        "Every horse (38 total) and two chariots were carved by hand by local volunteers — a remarkable community art project",
        "Caras Park along the Clark Fork River hosts the Saturday morning Missoula Farmers Market and summer outdoor events",
        "A Missoula institution since 1995; the $1 ride is a charming detour in a city known for its creative community"
    ],
    "Gates of the Mountains Viewpoint (en route, near Helena)": [
        "Dramatic limestone canyon on the Missouri River named by Meriwether Lewis in 1805 — 'the most remarkable cliffs we have yet seen'",
        "1,200-foot limestone walls rise vertically from the river, creating a corridor that seems to open like gates as you approach",
        "Boat tours run through the canyon in summer; the viewpoint from the road offers a preview of the spectacular geology",
        "Mountain goats, bighorn sheep, and bald eagles are frequently spotted along the canyon walls"
    ],
    "Hyalite Canyon Recreation Area": [
        "Popular recreation canyon south of Bozeman with a reservoir, waterfalls, hiking trails, and world-class ice climbing in winter",
        "Hyalite Reservoir is surrounded by forested mountains and several campgrounds; fishing and paddling are excellent",
        "Palisade Falls, a 60-foot waterfall reachable by a wheelchair-accessible trail, is the canyon's most popular attraction",
        "In winter, the frozen waterfalls become an ice climbing destination drawing climbers from around the world"
    ],
    "Peets Hill / Burke Park": [
        "Hilltop park in Bozeman with grassy slopes, wildflower meadows, and 360-degree views of the surrounding mountain ranges",
        "A favorite sunset spot for Bozeman locals; the Bridger Range, Gallatin Range, and Spanish Peaks are all visible",
        "The gentle trails are popular with dog walkers, families, and cross-country skiers in winter",
        "The hill is right in town — walk from Main Street to mountain views in 10 minutes"
    ],
    "Downtown Bozeman Main Street": [
        "Vibrant downtown with locally owned shops, restaurants, galleries, and a thriving craft brewery scene",
        "The American Computer & Robotics Museum and the Museum of the Rockies (world-class dinosaur collection) are must-visits",
        "Montana State University gives the town a youthful energy; the food scene rivals cities many times its size",
        "Surrounded by world-class skiing, fishing, and hiking — Bozeman is regularly ranked among the best mountain towns in America"
    ],
    "Palisade Falls": [
        "80-foot waterfall cascading down a columnar basalt cliff in Hyalite Canyon, reachable by a 1.2-mile wheelchair-accessible trail",
        "The basalt columns framing the falls are a textbook example of volcanic geology — formed by slow cooling of a lava flow",
        "In winter, the falls freeze into a dramatic ice curtain that draws ice climbers from across the region",
        "One of the most accessible waterfalls in Montana — the paved trail makes it enjoyable for all abilities"
    ],
    "Grotto Falls": [
        "Scenic waterfall in Hyalite Canyon reached by a moderate 2.6-mile round-trip hike through montane forest",
        "The falls drop into a natural grotto carved into the rock — you can walk behind the curtain of water",
        "Part of a chain of waterfalls in Hyalite Creek — ambitious hikers can continue upstream to additional cascades",
        "The trail passes through spruce-fir forest with wildflowers in summer and dramatic ice formations in winter"
    ],
    "Hyalite Reservoir": [
        "Mountain reservoir in a glacial cirque south of Bozeman, surrounded by peaks and dense forest",
        "Popular for fishing (cutthroat and grayling), kayaking, paddleboarding, and shoreline picnicking",
        "Several campgrounds ring the reservoir; the setting is quintessential Montana mountain lake scenery",
        "The road continues past the reservoir to trailheads for Palisade Falls, Grotto Falls, and the Hyalite Peak area"
    ],
    "Beehive Basin Trail (Big Sky detour)": [
        "Stunning 7-mile round-trip hike to a glacial cirque basin surrounded by alpine peaks near Big Sky Resort",
        "The trail climbs through wildflower meadows to a treeless alpine basin rimmed by 10,000-foot peaks",
        "Mountain goats are frequently spotted on the cliffs above the basin; moose browse in the willow thickets below",
        "One of the most rewarding day hikes in the Greater Yellowstone area — the meadows are extraordinary in July"
    ],
    "Little Bighorn Battlefield National Monument (en route)": [
        "Site of the June 1876 battle where Lakota, Northern Cheyenne, and Arapaho warriors defeated Lt. Col. George Custer's 7th Cavalry",
        "The battlefield is largely unchanged — white marble markers show where soldiers fell on the grassy hillsides",
        "The Indian Memorial (2003) honors the Native warriors who fought to preserve their way of life",
        "The visitor center and ranger programs present multiple perspectives — military history, Native oral traditions, and aftermath"
    ],
    "Bighorn Scenic Byway (US-14)": [
        "Dramatic mountain highway crossing the Bighorn Range between Lovell and Burgess Junction with alpine meadows and granite gorges",
        "The road climbs through colorful badlands, dense forest, and open alpine terrain above 9,000 feet",
        "Medicine Wheel/Medicine Mountain National Historic Landmark near the summit is a mysterious stone circle sacred to multiple tribes",
        "The Bighorns are less crowded than the Tetons or Yellowstone — genuine backcountry mountain scenery"
    ],
    "Historic Downtown Sheridan & The Mint Bar": [
        "Preserved Western downtown where the Mint Bar has served cowboys since 1907 with its original back bar and mounted trophies",
        "King's Saddlery sells handmade saddles and cowboy gear; their attached Don King Museum has Western artifacts and memorabilia",
        "Sheridan is a genuine ranching town — working cowboys in spurs and boots are not uncommon on Main Street",
        "WYO Theater, a beautifully restored 1923 vaudeville house, hosts live performances in an art deco setting"
    ],
    "Tongue River Trail & Kendrick Park": [
        "Trail along the Tongue River through Sheridan with connections to Kendrick Park's walking paths and picnic areas",
        "Kendrick Park has a swimming pool, playground, and shaded areas — a neighborhood park with mountain views",
        "The river trail is flat and easy, popular with dog walkers and families in all seasons",
        "The Bighorn Mountains rise to the west, providing a dramatic backdrop to this pleasant urban greenway"
    ],
    "Buffalo, WY -- Clear Creek Trail": [
        "Small Western town at the foot of the Bighorn Mountains with a walking trail along Clear Creek through the historic downtown",
        "The Occidental Hotel, built in 1878, hosted Teddy Roosevelt, Butch Cassidy, and Calamity Jane — it's still operating",
        "Clear Creek is a blue-ribbon trout stream; the trail offers easy access and pretty scenery through town",
        "Gateway to the Cloud Peak Wilderness and the Bighorn National Forest — genuine mountain-town character"
    ],
    "National Historic Trails Interpretive Center (Casper)": [
        "World-class museum in Casper telling the story of the Oregon, Mormon, California, and Pony Express trails",
        "Interactive exhibits include a simulated river crossing and a life-size covered wagon you can explore",
        "The center overlooks the North Platte River at the exact point where thousands of emigrants crossed in the 1840s-60s",
        "One of the best Western history museums in the country — it brings the pioneer experience to life"
    ],
    "Cheyenne, WY -- State Capitol": [
        "Wyoming's gold-domed capitol building in downtown Cheyenne, surrounded by historic buildings and Western heritage",
        "The capitol was built in 1888 and features murals, stained glass, and exhibits on Wyoming's history as the 'Equality State'",
        "Cheyenne Frontier Days, held annually since 1897, is the world's largest outdoor rodeo — 10 days of Western celebration",
        "The Frontier Days Old West Museum, historic depot district, and Big Boy steam locomotive #4004 are all walkable from the capitol"
    ],
}

def main():
    with open(f"data/attraction-images.json") as f:
        images = json.load(f)

    # Merge descriptions with images
    result = {}
    missing_desc = []
    missing_img = []

    for name, img_data in images.items():
        desc = DESCRIPTIONS.get(name)
        if not desc:
            missing_desc.append(name)
            desc = [img_data.get("description", name)]

        result[name] = {
            "photos": img_data["photos"],
            "type": img_data["type"],
            "desc": desc,
        }

    # Check for descriptions without images
    for name in DESCRIPTIONS:
        if name not in images:
            missing_img.append(name)

    outpath = "data/attraction-data.json"
    with open(outpath, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Merged {len(result)} attractions")
    print(f"With descriptions: {len(result) - len(missing_desc)}")
    if missing_desc:
        print(f"\nMissing descriptions ({len(missing_desc)}):")
        for n in missing_desc:
            print(f"  - {n}")
    if missing_img:
        print(f"\nDescriptions without images ({len(missing_img)}):")
        for n in missing_img:
            print(f"  - {n}")

    # Stats
    total_photos = sum(len(v["photos"]) for v in result.values())
    total_bullets = sum(len(v["desc"]) for v in result.values())
    size_mb = len(json.dumps(result)) / 1024 / 1024
    print(f"\nTotal: {total_photos} photos, {total_bullets} description bullets")
    print(f"Output: {outpath} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
