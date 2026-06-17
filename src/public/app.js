// Sabby Roadtrip — public site, slice 2.2
// Google-Maps-inspired light theme. Itinerary view = horizontal date-scroller
// chip strip + single Day card; Full Trip view = sidebar + Voyager-tile map.

const BIOME_ACCENTS = {
  gulf: "#1976d2",
  hill: "#7c8c40",
  west_desert: "#c47b3a",
  high_desert: "#b8553f",
  red_rock: "#c44f1f",
  pacific: "#1e88a8",
  mojave: "#c79a4a",
  rockies: "#3f6db5",
  plains: "#c19a3a",
};

const LOCATION_BIOME = {
  "Destin, FL": "gulf",
  "Lafayette, LA": "gulf",
  "Houston, TX": "gulf",
  "Little Rock, AR": "gulf",
  "Fredericksburg, TX": "hill",
  "Marfa, TX": "west_desert",
  "Santa Fe, NM": "high_desert",
  "Sedona, AZ": "red_rock",
  "Moab, UT": "red_rock",
  "San Diego, CA": "pacific",
  "Los Angeles, CA": "pacific",
  "Cambria, CA": "pacific",
  "Carmel-by-the-Sea, CA": "pacific",
  "Las Vegas, NV": "mojave",
  "Parker, CO": "rockies",
  "Hastings, NE": "plains",
};

const GM_BLUE = "#1a73e8";
const GM_GREEN = "#34a853";
const GM_RED = "#ea4335";

let trip, itinerary, geometries, todayPayload, config;
let mapInstance, mapDrawn = false;
let dayRendered = false;
let statsRendered = false;
let redrawStats = null;
let statsResizeBound = false;
let currentView = null;
let approvedSubmissions = [];
let activeSuggestContext = null;
let captchaWidgetId = null;
let pingTimer = null;
let selectedIndex = 0;
// segmentMiles["<legIdx>-<segIdx>"] = number of driving miles in that segment.
// cumulativeMilesByStop[legIdx][stopIdx] = miles driven up to and including that stop.
// dayMiles[dayIndex] = miles for that itinerary day (0 if rest).
let segmentMiles = {};
let cumulativeMilesByStop = [];
let dayMiles = [];
let totalMiles = 0;

async function init() {
  [trip, itinerary, geometries, todayPayload, config, approvedSubmissions] = await Promise.all([
    fetch("/api/trip").then((r) => r.json()),
    fetch("/api/itinerary").then((r) => r.json()),
    fetch("/api/geometries").then((r) => r.json()),
    fetch("/api/today").then((r) => r.json()),
    fetch("/api/config").then((r) => r.json()),
    fetch("/api/submissions").then((r) => r.json()).then((j) => j.submissions ?? []),
  ]);

  document.getElementById("trip-dates").textContent = trip.dates;

  computeDistances();

  selectedIndex = pickInitialIndex();
  renderDateRail();

  setupTabs();
  // Routing: open the view named by the URL (default = Full Trip). Views are
  // rendered lazily on first show so each Leaflet map measures a visible
  // container — the day card must render unhidden or its map breaks. popstate
  // re-derives the view from the path without writing history.
  window.addEventListener("popstate", () => applyView(viewFromPath(location.pathname)));
  applyView(viewFromPath(location.pathname));

  refreshPingStatus();
  pingTimer = setInterval(refreshPingStatus, 60_000);

  loadHCaptchaIfNeeded();
  setupSuggestModal();
}

function pickInitialIndex() {
  const ref = todayPayload.referenceDate;
  const days = itinerary.days;
  const todayIdx = days.findIndex((d) => d.date === ref);
  if (todayIdx >= 0) return todayIdx;
  const startIso = days[0].date;
  if (ref < startIso) return 0;
  return days.length - 1;
}

function setupTabs() {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => navigateToView(tab.dataset.view));
  });
}

// Each view has its own URL slug. "/" is canonical for Full Trip (left as-is on
// load); "/full-trip" is its explicit path; "/itinerary" is the day view.
const VIEW_TO_PATH = { trip: "/full-trip", day: "/itinerary", stats: "/stats" };

function viewFromPath(pathname) {
  if (pathname === "/itinerary") return "day";
  if (pathname === "/stats") return "stats";
  return "trip";
}

// User-initiated switch: push a new history entry, then apply. pushState happens
// ONLY here (tab clicks) — never on initial load or popstate — so browser
// back/forward stay consistent.
function navigateToView(view) {
  if (view === currentView) return;
  if (VIEW_TO_PATH[view]) history.pushState({}, "", VIEW_TO_PATH[view]);
  applyView(view);
}

// Toggle tabs/panels and lazily render the now-visible view. Never touches the
// URL, so it's safe to call from init and popstate.
function applyView(view) {
  currentView = view;
  document.querySelectorAll(".tab").forEach((t) =>
    t.setAttribute("aria-selected", String(t.dataset.view === view)),
  );
  document.querySelectorAll(".view").forEach((v) => (v.hidden = v.id !== `view-${view}`));
  if (view === "trip") {
    if (!mapDrawn) drawTripMap();
    setTimeout(() => mapInstance?.invalidateSize(), 50);
  } else if (view === "day") {
    if (!dayRendered) {
      renderSelectedDay();
      dayRendered = true;
    } else {
      setTimeout(() => dayMapInstance?.invalidateSize(), 50);
    }
  } else if (view === "stats") {
    if (!statsRendered) {
      renderStats();
      statsRendered = true;
    } else {
      redrawStats?.(); // re-measure in case the window resized while hidden
    }
  }
}

function renderDateRail() {
  const rail = document.getElementById("date-rail");
  rail.innerHTML = "";
  const todayIso = todayPayload.referenceDate;
  itinerary.days.forEach((d, i) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "date-chip";
    chip.setAttribute("role", "tab");
    chip.setAttribute("aria-selected", String(i === selectedIndex));
    chip.tabIndex = i === selectedIndex ? 0 : -1;
    if (d.date === todayIso) chip.classList.add("is-today");
    if (d.date < todayIso) chip.classList.add("is-past");
    if (d.isRestDay) chip.classList.add("is-rest");
    else chip.classList.add("is-drive");
    if (isCamping(d)) chip.classList.add("is-camping");
    chip.style.setProperty("--chip-accent", biomeAccent(d));

    const dt = new Date(d.date + "T00:00:00Z");
    const dow = dt.toLocaleDateString(undefined, { weekday: "short", timeZone: "UTC" }).toUpperCase();
    const dayN = dt.getUTCDate();
    const mon = dt.toLocaleDateString(undefined, { month: "short", timeZone: "UTC" }).toUpperCase();
    chip.innerHTML = `
      <span class="chip-dow"></span>
      <span class="chip-day"></span>
      <span class="chip-mon"></span>
      ${isCamping(d) ? `<span class="chip-camp" aria-label="Camping" title="Camping">⛺</span>` : ""}
      <span class="chip-bar" aria-hidden="true"></span>
    `;
    chip.querySelector(".chip-dow").textContent = dow;
    chip.querySelector(".chip-day").textContent = String(dayN);
    chip.querySelector(".chip-mon").textContent = mon;
    chip.addEventListener("click", () => selectChip(i, false));
    chip.addEventListener("keydown", onChipKeydown);
    rail.appendChild(chip);
  });
  scrollChipIntoView(rail);
}

function isCamping(day) {
  const lodging = (day?.lodging ?? "").toLowerCase();
  return lodging.includes("camping") || lodging.includes("tent") || lodging.includes("campground");
}

function selectChip(i, focus) {
  selectedIndex = Math.max(0, Math.min(itinerary.days.length - 1, i));
  renderDateRail();
  renderSelectedDay();
  const rail = document.getElementById("date-rail");
  scrollChipIntoView(rail);
  if (focus) rail.children[selectedIndex]?.focus();
}

function onChipKeydown(ev) {
  const last = itinerary.days.length - 1;
  switch (ev.key) {
    case "ArrowRight": ev.preventDefault(); selectChip(selectedIndex + 1, true); break;
    case "ArrowLeft":  ev.preventDefault(); selectChip(selectedIndex - 1, true); break;
    case "Home":       ev.preventDefault(); selectChip(0, true); break;
    case "End":        ev.preventDefault(); selectChip(last, true); break;
  }
}

function scrollChipIntoView(rail) {
  const chip = rail.children[selectedIndex];
  if (!chip) return;
  const railRect = rail.getBoundingClientRect();
  const chipRect = chip.getBoundingClientRect();
  if (chipRect.left < railRect.left || chipRect.right > railRect.right) {
    rail.scrollTo({ left: chip.offsetLeft - rail.clientWidth / 2 + chip.clientWidth / 2, behavior: "smooth" });
  }
}

function renderSelectedDay() {
  const day = itinerary.days[selectedIndex];
  const host = document.getElementById("day-card-host");
  if (!day) {
    host.innerHTML = "";
    return;
  }
  const accent = biomeAccent(day);
  document.documentElement.style.setProperty("--day-accent", accent);

  const driveLabel = day.isRestDay ? "Rest day" : day.drivingHours;
  const subs = approvedSubmissions.filter(
    (s) => s.for_date === day.date || (s.for_date == null && s.for_stop && (s.for_stop === day.start || s.for_stop === day.end)),
  );

  host.innerHTML = `
    <article class="day-card">
      <div class="day-stripe"></div>
      <div class="day-body">
        <div class="day-eyebrow">
          <span class="dot"></span>
          <span>${escapeHtml(day.day || prettyDate(day.date))}</span>
          ${day.isRestDay ? '<span class="badge badge-rest">Rest</span>' : ""}
          ${isCamping(day) ? '<span class="badge badge-camp">⛺ Camping</span>' : ""}
        </div>
        <h1 class="day-title">${prettyDate(day.date)}</h1>
        <div class="day-route">
          <span>${escapeHtml(day.start || "—")}</span>
          <span class="day-arrow">→</span>
          <span>${escapeHtml(day.end || "—")}</span>
        </div>
        <div class="day-stats">
          <div><div class="stat-label">Driving</div><div class="stat-value">${escapeHtml(driveLabel || "—")}</div></div>
          ${dayMiles[selectedIndex] > 0 ? `<div><div class="stat-label">Distance</div><div class="stat-value">${formatMi(dayMiles[selectedIndex])}</div></div>` : ""}
          <div><div class="stat-label">Lodging</div><div class="stat-value">${escapeHtml(formatLodging(day.lodging))}</div></div>
          ${day.daytrip ? `<div><div class="stat-label">Daytrip</div><div class="stat-value">${escapeHtml(day.daytrip)}</div></div>` : ""}
        </div>
        <div class="day-map" id="day-map"></div>
        <div class="day-cta">
          <button class="btn-suggest" data-date="${day.date}" data-stop="${escapeHtml(day.end || day.start || "")}">+ Suggest a place</button>
        </div>
        ${renderSuggestions(subs)}
      </div>
    </article>
  `;
  host.querySelector(".btn-suggest")?.addEventListener("click", (ev) => {
    const b = ev.currentTarget;
    openSuggestModal({ date: b.dataset.date, stop: b.dataset.stop });
  });
  drawDayMap(day);
  renderProgressStrip();
}

function renderProgressStrip() {
  const el = document.getElementById("progress-strip");
  if (!el) return;
  const totalDays = itinerary.days.length;
  const dayIdx = selectedIndex; // 0-based; "Day N" = dayIdx + 1
  const dayN = dayIdx + 1;
  const dayPct = Math.min(100, (dayN / totalDays) * 100);
  const milesSoFar = milesThroughDay(dayIdx);
  const milePct = Math.min(100, totalMiles > 0 ? (milesSoFar / totalMiles) * 100 : 0);
  el.innerHTML = `
    <div class="progress-row">
      <div class="progress-cell">
        <div class="progress-label">Day</div>
        <div class="progress-value">${dayN}<span class="progress-of"> / ${totalDays}</span></div>
        <div class="progress-bar"><div class="progress-bar-fill" style="width:${dayPct.toFixed(1)}%"></div></div>
        <div class="progress-pct">${dayPct.toFixed(0)}%</div>
      </div>
      <div class="progress-cell">
        <div class="progress-label">Miles driven</div>
        <div class="progress-value">${formatMi(milesSoFar)}<span class="progress-of"> / ${formatMi(totalMiles)}</span></div>
        <div class="progress-bar"><div class="progress-bar-fill progress-bar-fill-miles" style="width:${milePct.toFixed(1)}%"></div></div>
        <div class="progress-pct">${milePct.toFixed(0)}%</div>
      </div>
    </div>
  `;
}

let dayMapInstance = null;
function drawDayMap(day) {
  if (dayMapInstance) {
    dayMapInstance.remove();
    dayMapInstance = null;
  }
  const el = document.getElementById("day-map");
  if (!el || !day.startCoords) return;

  dayMapInstance = L.map(el, {
    zoomControl: false,
    attributionControl: false,
    scrollWheelZoom: false,
    dragging: window.matchMedia("(pointer: fine)").matches,
  });
  L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", {
    subdomains: "abcd", maxZoom: 19,
  }).addTo(dayMapInstance);

  const isDrive = !day.isRestDay && day.endCoords && !coordsEqual(day.startCoords, day.endCoords);

  if (isDrive) {
    const seg = findDaySegment(day);
    const line = seg?.geometry ?? [day.startCoords, day.endCoords];
    L.polyline(line, { color: GM_BLUE, weight: 4, opacity: 0.9 }).addTo(dayMapInstance);
    L.circleMarker(day.startCoords, {
      radius: 7, color: "#fff", weight: 2, fillColor: GM_GREEN, fillOpacity: 1,
    }).addTo(dayMapInstance);
    L.circleMarker(day.endCoords, {
      radius: 7, color: "#fff", weight: 2, fillColor: GM_RED, fillOpacity: 1,
    }).addTo(dayMapInstance);
    dayMapInstance.fitBounds(line, { padding: [24, 24] });
  } else {
    L.circleMarker(day.startCoords, {
      radius: 8, color: "#fff", weight: 2, fillColor: GM_BLUE, fillOpacity: 1,
    }).addTo(dayMapInstance);
    dayMapInstance.setView(day.startCoords, 9);
  }
}

function coordsEqual(a, b) {
  return Math.abs(a[0] - b[0]) < 0.001 && Math.abs(a[1] - b[1]) < 0.001;
}

function haversineMi(a, b) {
  const R = 3958.7613; // Earth radius in miles
  const toRad = (d) => (d * Math.PI) / 180;
  const dLat = toRad(b[0] - a[0]);
  const dLng = toRad(b[1] - a[1]);
  const lat1 = toRad(a[0]);
  const lat2 = toRad(b[0]);
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

function polylineMi(pts) {
  let mi = 0;
  for (let i = 0; i < pts.length - 1; i++) mi += haversineMi(pts[i], pts[i + 1]);
  return mi;
}

function computeDistances() {
  // segmentMiles is the single source of truth. Two derivations follow:
  // cumulativeMilesByStop walks legs/segments in order (drives the Full Trip
  // sidebar), and dayMiles walks itinerary days mapping each to a segment
  // (drives the day-card stat + progress strip via milesThroughDay).
  // Both must consume the same segmentMiles map — keep that invariant if
  // ever editing.
  segmentMiles = {};
  totalMiles = 0;
  for (const [key, pts] of Object.entries(geometries.trip ?? {})) {
    const mi = polylineMi(pts);
    segmentMiles[key] = mi;
    totalMiles += mi;
  }

  cumulativeMilesByStop = trip.legs.map((leg, li) => {
    const out = new Array(leg.stops.length).fill(0);
    // Cumulative miles at each stop = sum of all segments traversed up to that point
    // across all preceding legs + the current leg's segments up to (stopIdx - 1).
    let running = 0;
    for (let prevLeg = 0; prevLeg < li; prevLeg++) {
      const prev = trip.legs[prevLeg];
      for (let s = 0; s < prev.stops.length - 1; s++) {
        running += segmentMiles[`${prevLeg}-${s}`] ?? 0;
      }
    }
    out[0] = running;
    for (let si = 1; si < leg.stops.length; si++) {
      running += segmentMiles[`${li}-${si - 1}`] ?? 0;
      out[si] = running;
    }
    return out;
  });

  dayMiles = itinerary.days.map((day) => {
    if (day.isRestDay) return 0;
    const seg = findDaySegment(day);
    if (!seg) return 0;
    return segmentMiles[`${seg.legIdx}-${seg.segIdx}`] ?? 0;
  });
}

function milesThroughDay(idx) {
  let mi = 0;
  for (let i = 0; i <= idx; i++) mi += dayMiles[i] ?? 0;
  return mi;
}

function formatMi(mi) {
  if (mi < 1) return "0 mi";
  if (mi < 10) return `${mi.toFixed(1)} mi`;
  return `${Math.round(mi).toLocaleString()} mi`;
}

function coordsNear(stop, coords, tol = 0.05) {
  return Math.abs(stop.lat - coords[0]) < tol && Math.abs(stop.lng - coords[1]) < tol;
}

function findDaySegment(day) {
  if (!day.startCoords || !day.endCoords) return null;
  for (let li = 0; li < trip.legs.length; li++) {
    const leg = trip.legs[li];
    for (let si = 0; si < leg.stops.length - 1; si++) {
      if (coordsNear(leg.stops[si], day.startCoords) && coordsNear(leg.stops[si + 1], day.endCoords)) {
        const geometry = geometries.trip?.[`${li}-${si}`];
        return geometry ? { legIdx: li, segIdx: si, geometry } : null;
      }
    }
  }
  return null;
}

function biomeAccent(day) {
  const key = LOCATION_BIOME[day?.end] ?? LOCATION_BIOME[day?.start] ?? null;
  return key ? BIOME_ACCENTS[key] : GM_BLUE;
}

function renderSuggestions(subs) {
  if (subs.length === 0) return "";
  return `
    <section class="day-suggestions">
      <h3>From visitors</h3>
      <ul>
        ${subs.map((s) => `
          <li>
            <strong>${escapeHtml(s.name)}</strong>
            ${s.submitter_name ? `<span class="suggester">— ${escapeHtml(s.submitter_name)}</span>` : ""}
            ${s.description ? `<div class="suggestion-body">${escapeHtml(s.description)}</div>` : ""}
            ${s.url ? `<a class="suggestion-link" href="${encodeURI(s.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(prettyHost(s.url))}</a>` : ""}
          </li>`).join("")}
      </ul>
    </section>`;
}

function prettyHost(url) {
  try { return new URL(url).host; } catch { return url; }
}

function formatLodging(s) {
  if (!s) return "—";
  return s.replace(/^(hotel|airbnb|camping|home):?\s*/i, (m, kind) => `${kind[0].toUpperCase()}${kind.slice(1)} · `);
}

function prettyDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso + "T00:00:00Z");
  return d.toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric", timeZone: "UTC" });
}

function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

async function refreshPingStatus() {
  try {
    const j = await fetch("/api/location").then((r) => r.json());
    const el = document.getElementById("ping-status");
    if (j.ping?.ts) {
      const mins = j.ping.minutesAgo ?? Math.max(0, Math.round((Date.now() - new Date(j.ping.ts).getTime()) / 60000));
      const where = j.ping.label ? ` · ${j.ping.label}` : "";
      el.textContent = `Last ping ${mins === 0 ? "just now" : `${mins} min ago`}${where}`;
    } else {
      el.textContent = j.message ?? "Last ping unknown";
    }
  } catch {
    /* ignore */
  }
}

let segmentLines = [];
let highlightedSegment = null;

function drawTripMap() {
  mapDrawn = true;
  mapInstance = L.map("map", { zoomControl: false }).setView([36, -100], 5);
  L.control.zoom({ position: "topright" }).addTo(mapInstance);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", {
    attribution: "&copy; OpenStreetMap, &copy; CARTO",
    subdomains: "abcd",
    maxZoom: 19,
  }).addTo(mapInstance);

  const allCoords = [];
  const legend = document.getElementById("trip-stops");
  legend.innerHTML = "";
  segmentLines = [];

  const isLastLegIdx = trip.legs.length - 1;

  trip.legs.forEach((leg, li) => {
    const block = document.createElement("div");
    block.className = "leg-block";
    block.innerHTML = `<div class="leg-name"></div>`;
    block.querySelector(".leg-name").textContent = leg.name;
    leg.stops.forEach((stop, si) => {
      allCoords.push([stop.lat, stop.lng]);
      const color = stop.type === "start" ? GM_GREEN : stop.type === "end" ? GM_RED : GM_BLUE;
      const marker = L.circleMarker([stop.lat, stop.lng], {
        radius: stop.type === "start" || stop.type === "end" ? 8 : 6,
        color: "#fff",
        weight: 2,
        fillColor: color,
        fillOpacity: 1,
      }).addTo(mapInstance);
      marker.bindPopup(`<b>${escapeHtml(stop.name)}</b><br>${escapeHtml(stop.address)}`);

      const isLastInLastLeg = li === isLastLegIdx && si === leg.stops.length - 1;
      const dateLabel = stopDateLabel(stop, li, si, leg, isLastInLastLeg);
      const cumMiles = cumulativeMilesByStop[li]?.[si] ?? 0;
      const milesLabel = cumMiles > 0 ? formatMi(cumMiles) : "";
      const canHighlight = si > 0; // first stop of each leg has no inbound segment shown distinctly

      const row = document.createElement("div");
      row.className = `stop-row ${stop.type}`;
      row.innerHTML = `
        <span class="stop-bullet"></span>
        <div class="stop-text">
          <span class="stop-name"></span>
          <span class="stop-date"></span>
        </div>
        ${canHighlight ? `<button class="route-icon" type="button" data-leg="${li}" data-seg="${si - 1}" aria-label="Highlight route to ${escapeHtml(stop.name)}" title="Highlight route to ${escapeHtml(stop.name)}">
          <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true" fill="currentColor">
            <path d="M21.71 11.29l-9-9a.996.996 0 0 0-1.41 0l-9 9a.996.996 0 0 0 0 1.41l9 9c.39.39 1.02.39 1.41 0l9-9c.39-.38.39-1.01 0-1.41zM14 14.5V12h-4v3H8v-4c0-.55.45-1 1-1h5V7.5l3.5 3.5-3.5 3.5z"/>
          </svg>
        </button>` : ""}
      `;
      row.querySelector(".stop-name").textContent = stop.name;
      row.querySelector(".stop-date").textContent =
        milesLabel ? `${dateLabel} · ${milesLabel}` : dateLabel;
      row.querySelector(".stop-text").addEventListener("click", () => {
        clearSegmentHighlight();
        mapInstance.flyTo([stop.lat, stop.lng], 9, { duration: 0.8 });
      });
      const routeBtn = row.querySelector(".route-icon");
      if (routeBtn) {
        routeBtn.addEventListener("click", (ev) => {
          ev.stopPropagation();
          toggleSegmentHighlight(li, si - 1);
        });
      }
      block.appendChild(row);

      if (si < leg.stops.length - 1) {
        const segKey = `${li}-${si}`;
        const next = leg.stops[si + 1];
        const segCoords = geometries.trip?.[segKey] ?? [
          [stop.lat, stop.lng],
          [next.lat, next.lng],
        ];
        const polyline = L.polyline(segCoords, {
          color: GM_BLUE, weight: 4, opacity: 0.85,
        }).addTo(mapInstance);
        segmentLines.push({ legIdx: li, segIdx: si, polyline });
      }
    });
    legend.appendChild(block);
  });

  trip.daytrips.forEach((dt) => {
    const m = L.circleMarker([dt.lat, dt.lng], {
      radius: 4, color: "#fff", weight: 1.5, fillColor: "#fbbc04", fillOpacity: 0.95,
    }).addTo(mapInstance);
    m.bindPopup(`<b>${escapeHtml(dt.name)}</b><br>Daytrip near ${escapeHtml(dt.nearStop)}`);
  });

  mapInstance.fitBounds(allCoords, { padding: [40, 40] });
}

function toggleSegmentHighlight(legIdx, segIdx) {
  const same = highlightedSegment && highlightedSegment.legIdx === legIdx && highlightedSegment.segIdx === segIdx;
  if (same) {
    clearSegmentHighlight();
    return;
  }
  highlightedSegment = { legIdx, segIdx };
  segmentLines.forEach(({ legIdx: li, segIdx: si, polyline }) => {
    const match = li === legIdx && si === segIdx;
    polyline.setStyle({
      color: match ? GM_RED : GM_BLUE,
      weight: match ? 6 : 4,
      opacity: match ? 1 : 0.18,
    });
    if (match) polyline.bringToFront();
  });
  document.querySelectorAll(".route-icon").forEach((btn) => btn.classList.remove("active"));
  document.querySelector(`.route-icon[data-leg="${legIdx}"][data-seg="${segIdx}"]`)?.classList.add("active");
  const seg = segmentLines.find((s) => s.legIdx === legIdx && s.segIdx === segIdx);
  if (seg) mapInstance.fitBounds(seg.polyline.getBounds(), { padding: [60, 60] });
}

function clearSegmentHighlight() {
  highlightedSegment = null;
  segmentLines.forEach(({ polyline }) => {
    polyline.setStyle({ color: GM_BLUE, weight: 4, opacity: 0.85 });
  });
  document.querySelectorAll(".route-icon.active").forEach((btn) => btn.classList.remove("active"));
}

function stopDateLabel(stop, legIdx, stopIdx, leg, isLastInLastLeg) {
  const days = itinerary.days;
  if (legIdx === 0 && stopIdx === 0) return shortDate(days[0].date);
  if (isLastInLastLeg) return shortDate(days[days.length - 1].date);
  const sleepNights = days
    .filter((d) => d.endCoords && coordsNear(stop, d.endCoords))
    .map((d) => d.date)
    .sort();
  if (sleepNights.length === 0) return "";
  if (sleepNights.length === 1) return shortDate(sleepNights[0]);
  return shortDateRange(sleepNights[0], sleepNights[sleepNights.length - 1]);
}

function shortDate(iso) {
  const d = new Date(iso + "T00:00:00Z");
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric", timeZone: "UTC" });
}

function shortDateRange(isoA, isoB) {
  const a = new Date(isoA + "T00:00:00Z");
  const b = new Date(isoB + "T00:00:00Z");
  if (a.getUTCMonth() === b.getUTCMonth()) {
    const m = a.toLocaleDateString(undefined, { month: "short", timeZone: "UTC" });
    return `${m} ${a.getUTCDate()} – ${b.getUTCDate()}`;
  }
  return `${shortDate(isoA)} – ${shortDate(isoB)}`;
}

// ---- Suggest modal ----

function setupSuggestModal() {
  document.getElementById("suggest-close").addEventListener("click", closeSuggestModal);
  document.getElementById("suggest-modal").addEventListener("click", (ev) => {
    if (ev.target.id === "suggest-modal") closeSuggestModal();
  });
  document.getElementById("suggest-form").addEventListener("submit", onSuggestSubmit);
}

function loadHCaptchaIfNeeded() {
  if (!config?.captchaEnabled || !config.hcaptchaSitekey) return;
  const s = document.getElementById("hcaptcha-loader");
  s.src = "https://js.hcaptcha.com/1/api.js?render=explicit";
  s.onload = () => {
    const slot = document.getElementById("captcha-slot");
    captchaWidgetId = window.hcaptcha.render(slot, {
      sitekey: config.hcaptchaSitekey,
      theme: "light",
    });
  };
}

function openSuggestModal(ctx) {
  activeSuggestContext = ctx;
  const modal = document.getElementById("suggest-modal");
  const ctxLabel = ctx.date
    ? `For ${prettyDate(ctx.date)}${ctx.stop ? ` · ${ctx.stop}` : ""}`
    : `Anywhere on the trip`;
  document.getElementById("suggest-context").textContent = ctxLabel;
  document.getElementById("suggest-form").reset();
  document.getElementById("suggest-result").hidden = true;
  modal.hidden = false;
  modal.querySelector('input[name="name"]').focus();
  if (captchaWidgetId !== null && window.hcaptcha) window.hcaptcha.reset(captchaWidgetId);
}

function closeSuggestModal() {
  document.getElementById("suggest-modal").hidden = true;
  activeSuggestContext = null;
}

async function onSuggestSubmit(ev) {
  ev.preventDefault();
  const form = ev.currentTarget;
  const data = Object.fromEntries(new FormData(form));
  const result = document.getElementById("suggest-result");
  result.hidden = true;
  result.classList.remove("error", "success");

  const payload = {
    name: data.name?.trim(),
    description: data.description?.trim() || null,
    url: data.url?.trim() || null,
    submitter_name: data.submitter_name?.trim() || null,
    for_date: activeSuggestContext?.date || null,
    for_stop: activeSuggestContext?.stop || null,
  };
  if (config?.captchaEnabled && captchaWidgetId !== null && window.hcaptcha) {
    payload.captcha = window.hcaptcha.getResponse(captchaWidgetId);
    if (!payload.captcha) {
      showResult(result, "Please complete the captcha.", "error");
      return;
    }
  }
  if (!payload.name) {
    showResult(result, "Place name is required.", "error");
    return;
  }
  const r = await fetch("/api/submissions", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (r.ok) {
    showResult(result, "Thanks — your suggestion is in the moderation queue.", "success");
    form.reset();
    setTimeout(closeSuggestModal, 1800);
  } else if (r.status === 429) {
    showResult(result, "Slow down — too many submissions from this network.", "error");
  } else {
    const j = await r.json().catch(() => ({}));
    showResult(result, j.error ?? "Something went wrong, please try again.", "error");
  }
}

function showResult(el, text, kind) {
  el.textContent = text;
  el.classList.add(kind);
  el.hidden = false;
}

// ---- Trip Stats view ----
// All charts are hand-rolled inline SVG drawn in a fixed viewBox and scaled to
// 100% width (resolution-independent — no container measurement needed).
// Rendered lazily on first show. Drive times are PLANNED values parsed from the
// itinerary's free-text drivingHours (human-entered, some rounded) — surfaced as
// "planned", never as measured.

const DRIVE_RE = /^(\d+(?:\.\d+)?)\s*hrs?(?:\s+(\d+)\s*min)?$/i;
function driveMinutes(raw) {
  const m = DRIVE_RE.exec((raw ?? "").trim());
  if (!m) return 0; // "N/A" (rest days) and anything unparseable -> 0
  return Math.round(parseFloat(m[1]) * 60 + (m[2] ? parseInt(m[2], 10) : 0));
}

function formatHrsMin(min) {
  const h = Math.floor(min / 60);
  const m = Math.round(min % 60);
  return m === 0 ? `${h}h` : `${h}h ${m}m`;
}

// Lodging categorizer — maps the itinerary's free-text lodging field to a small
// set of buckets. Mapping (confirmed against the data, nights in parens):
//   contains "camp"             -> camping  ("camping" x4)
//   contains "airbnb"           -> airbnb   ("airbnb" x19)
//   contains "hotel"            -> hotel    ("hotel" / "hotel: El Rey Court" ... x7)
//   contains "nathan"/"abigail" -> family   ("Nathan's" x4, "Abigail's or this" x2)
//   exactly "home"              -> home     ("home" x1, the Destin homecoming)
//   "" or unrecognized          -> other    (the one blank Las Vegas night x1)
const LODGING_BUCKETS = [
  { key: "airbnb", label: "Airbnb", color: "#1e88a8" },
  { key: "hotel", label: "Hotel", color: "#1a73e8" },
  { key: "family", label: "Family/friends", color: "#34a853" },
  { key: "camping", label: "Camping", color: "#c79a4a" },
  { key: "home", label: "Home", color: "#ea4335" },
  { key: "other", label: "Other", color: "#9aa0a6" },
];
function lodgingBucket(raw) {
  const s = (raw ?? "").trim().toLowerCase();
  if (!s) return "other";
  if (s.includes("camp")) return "camping";
  if (s.includes("airbnb")) return "airbnb";
  if (s.includes("hotel")) return "hotel";
  if (s.includes("nathan") || s.includes("abigail")) return "family";
  if (s === "home") return "home";
  return "other";
}

const BIOME_LABELS = {
  gulf: "Gulf Coast", hill: "Hill Country", west_desert: "West TX Desert",
  high_desert: "High Desert", red_rock: "Red Rock", pacific: "Pacific Coast",
  mojave: "Mojave", rockies: "Rockies", plains: "Great Plains",
};

const HOME_LOCATION = "Destin, FL";

function renderStats() {
  const host = document.getElementById("view-stats");
  if (!host) return;
  const days = itinerary.days;
  const n = days.length;
  // "Stay" stats exclude the homecoming night (arriving home isn't a trip stay);
  // journey totals below keep all `days` so the final drive home still counts.
  const stayDays = days.filter((d) => d.end !== HOME_LOCATION);

  // Derived series (cumulative arrays filled as a side effect of reduce).
  const driveMin = days.map((d) => (d.isRestDay ? 0 : driveMinutes(d.drivingHours)));
  const cumMiles = [];
  const cumMin = [];
  dayMiles.reduce((acc, v, i) => (cumMiles[i] = acc + (v || 0)), 0);
  driveMin.reduce((acc, v, i) => (cumMin[i] = acc + v), 0);
  const totalDriveMin = cumMin[n - 1] ?? 0;

  const driveDays = days.filter((d) => !d.isRestDay).length;
  const restDays = n - driveDays;
  const daytrips = days.filter((d) => d.daytrip).length;

  // Nights per overnight (end) location; built in trip order then sorted desc.
  const nightIdx = new Map();
  const nights = [];
  stayDays.forEach((d) => {
    if (!nightIdx.has(d.end)) { nightIdx.set(d.end, nights.length); nights.push({ label: d.end, value: 0 }); }
    nights[nightIdx.get(d.end)].value++;
  });
  const overnightStops = nights.length;
  const nightsSorted = [...nights].sort((a, b) => b.value - a.value);

  // Longest planned drive day.
  let longest = { min: 0, label: "" };
  days.forEach((d, i) => {
    if (driveMin[i] > longest.min) longest = { min: driveMin[i], label: `${d.start} → ${d.end}` };
  });

  // Nights by lodging type.
  const lodgeCounts = new Map(LODGING_BUCKETS.map((b) => [b.key, 0]));
  stayDays.forEach((d) => {
    const k = lodgingBucket(d.lodging);
    lodgeCounts.set(k, lodgeCounts.get(k) + 1);
  });
  const lodgeData = LODGING_BUCKETS.map((b) => ({ ...b, value: lodgeCounts.get(b.key) })).filter((b) => b.value > 0);

  // Days per biome/region (by overnight location), sorted desc.
  const biomeCounts = new Map();
  stayDays.forEach((d) => {
    const key = LOCATION_BIOME[d.end] ?? LOCATION_BIOME[d.start];
    if (key) biomeCounts.set(key, (biomeCounts.get(key) ?? 0) + 1);
  });
  const biomeData = [...biomeCounts.entries()]
    .map(([key, value]) => ({ label: BIOME_LABELS[key] ?? key, value, color: BIOME_ACCENTS[key] ?? GM_BLUE }))
    .sort((a, b) => b.value - a.value);

  const dateShort = days.map((d) => shortDate(d.date));

  const tiles = [
    ["Total distance", formatMi(totalMiles)],
    ["Drive time (planned)", formatHrsMin(totalDriveMin)],
    ["Days on the road", String(n)],
    ["Driving vs rest", `${driveDays} drive · ${restDays} rest`],
    ["Overnight stops", String(overnightStops)],
    ["Daytrips", String(daytrips)],
    ["Longest drive (planned)", `${formatHrsMin(longest.min)} · ${longest.label}`],
  ];

  // Each chart draws into a measured pixel width (viewBox == css px, so labels
  // stay crisp at any column width and on mobile) — the same measure-on-show
  // approach the maps use. Redrawn on resize and whenever the view re-shows.
  // `wide` charts (time series) render 16:9 in the expand modal; the rest keep
  // their natural aspect. draw(w, h) lets the modal request a larger size.
  const charts = [
    { title: "Distance per day", sub: "Miles driven each day (rest days = 0)", wide: true,
      draw: (w, h) => barChart(dayMiles.map((v, i) => ({ value: v, title: `${dateShort[i]}: ${formatMi(v)}` })),
        { unit: "mi", color: "var(--gm-blue)", labels: dateShort, w, h }) },
    { title: "Cumulative distance", sub: "Total miles driven over the trip", wide: true,
      draw: (w, h) => lineChart(cumMiles, { unit: "mi", labels: dateShort, color: "var(--gm-blue)", w, h }) },
    { title: "Drive time per day", sub: "Planned drive time from the itinerary (human-entered)", wide: true,
      draw: (w, h) => barChart(driveMin.map((v, i) => ({ value: v, title: `${dateShort[i]}: ${formatHrsMin(v)}` })),
        { fmt: formatHrsMin, color: "var(--gm-green)", labels: dateShort, w, h }) },
    { title: "Cumulative drive time", sub: "Planned drive time accumulated over the trip", wide: true,
      draw: (w, h) => lineChart(cumMin, { fmt: formatHrsMin, labels: dateShort, color: "var(--gm-green)", w, h }) },
    { title: "Nights per location", sub: "Frequency of overnight stays by stop",
      draw: (w) => hBarChart(nightsSorted, { homeLabel: HOME_LOCATION, w }) },
    { title: "Nights by lodging type", sub: "What kind of place we slept each night",
      draw: () => donutChart(lodgeData, stayDays.length, "nights") },
    { title: "Days per region", sub: "Days spent in each biome/region",
      draw: (w) => hBarChart(biomeData, { w }) },
  ];
  modalCharts = charts;

  host.innerHTML = `
    <div class="stats-wrap">
      <h1 class="stats-title">Trip by the numbers</h1>
      <section class="stat-tiles">
        ${tiles.map(([k, v]) => `
          <div class="stat-tile">
            <div class="stat-tile-label">${escapeHtml(k)}</div>
            <div class="stat-tile-value">${escapeHtml(v)}</div>
          </div>`).join("")}
      </section>
      <div class="chart-grid">
        ${charts.map((c, i) => `
          <figure class="chart-card" data-i="${i}" role="group" aria-label="${escapeHtml(c.title)}">
            <button class="chart-expand" type="button" aria-label="Expand ${escapeHtml(c.title)}" title="Expand">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/></svg>
            </button>
            <figcaption><span class="chart-title">${escapeHtml(c.title)}</span><span class="chart-sub">${escapeHtml(c.sub)}</span></figcaption>
            <div class="chart-slot" data-i="${i}"></div>
          </figure>`).join("")}
      </div>
    </div>
  `;

  redrawStats = () => host.querySelectorAll(".chart-slot").forEach((slot) => {
    const w = Math.max(280, Math.round(slot.clientWidth || 320));
    slot.innerHTML = charts[Number(slot.dataset.i)].draw(w);
  });
  redrawStats();

  // Click anywhere on a card (or its expand button, which bubbles here) opens
  // the chart in the lightbox.
  host.querySelectorAll(".chart-card").forEach((card) => {
    card.addEventListener("click", () => openChartModal(Number(card.dataset.i)));
  });
  setupChartModal();

  if (!statsResizeBound) {
    statsResizeBound = true;
    let t;
    window.addEventListener("resize", () => {
      if (currentView !== "stats") return;
      clearTimeout(t);
      t = setTimeout(() => redrawStats?.(), 150);
    });
  }
}

// Round a max value up to a clean axis bound.
function niceMax(v) {
  if (v <= 0) return 1;
  const pow = Math.pow(10, Math.floor(Math.log10(v)));
  for (const s of [1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10]) {
    if (v <= s * pow) return s * pow;
  }
  return 10 * pow;
}

// Vertical bar chart. data = [{ value, title }].
function barChart(data, opts = {}) {
  const W = opts.w ?? 720, H = opts.h ?? 240, padL = 52, padR = 10, padT = 14, padB = 26;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const unit = opts.unit ? " " + opts.unit : "";
  const fmt = opts.fmt ?? ((v) => `${Math.round(v).toLocaleString()}${unit}`);
  const n = data.length;
  const max = niceMax(Math.max(1, ...data.map((d) => d.value)));
  const slot = plotW / n;
  const bw = Math.max(1, slot - (n > 30 ? 1 : 3));
  const yOf = (v) => padT + plotH - (v / max) * plotH;
  const labels = opts.labels ?? [];
  const grid = [0, max / 2, max].map((t) =>
    `<line x1="${padL}" y1="${yOf(t).toFixed(1)}" x2="${W - padR}" y2="${yOf(t).toFixed(1)}" class="chart-grid-line"/>` +
    `<text x="${padL - 6}" y="${(yOf(t) + 3).toFixed(1)}" class="chart-axis" text-anchor="end">${escapeHtml(fmt(t))}</text>`).join("");
  const bars = data.map((d, i) => {
    if (d.value <= 0) return "";
    const bx = padL + i * slot + (slot - bw) / 2;
    return `<rect x="${bx.toFixed(1)}" y="${yOf(d.value).toFixed(1)}" width="${bw.toFixed(1)}" height="${((d.value / max) * plotH).toFixed(1)}" rx="1.5" fill="${opts.color ?? "var(--gm-blue)"}"><title>${escapeHtml(d.title ?? fmt(d.value))}</title></rect>`;
  }).join("");
  const xl = `<text x="${padL}" y="${H - 8}" class="chart-axis" text-anchor="start">${escapeHtml(labels[0] ?? "")}</text>` +
    `<text x="${W - padR}" y="${H - 8}" class="chart-axis" text-anchor="end">${escapeHtml(labels[n - 1] ?? "")}</text>`;
  return `<svg class="chart" viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet" role="img">${grid}${bars}${xl}</svg>`;
}

// Cumulative line + area chart. values = number[].
function lineChart(values, opts = {}) {
  const W = opts.w ?? 720, H = opts.h ?? 240, padL = 56, padR = 14, padT = 16, padB = 26;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const unit = opts.unit ? " " + opts.unit : "";
  const fmt = opts.fmt ?? ((v) => `${Math.round(v).toLocaleString()}${unit}`);
  const n = values.length;
  const max = niceMax(Math.max(1, ...values));
  const xOf = (i) => padL + (n <= 1 ? 0 : (i / (n - 1)) * plotW);
  const yOf = (v) => padT + plotH - (v / max) * plotH;
  const grid = [0, max / 2, max].map((t) =>
    `<line x1="${padL}" y1="${yOf(t).toFixed(1)}" x2="${W - padR}" y2="${yOf(t).toFixed(1)}" class="chart-grid-line"/>` +
    `<text x="${padL - 6}" y="${(yOf(t) + 3).toFixed(1)}" class="chart-axis" text-anchor="end">${escapeHtml(fmt(t))}</text>`).join("");
  const pts = values.map((v, i) => `${xOf(i).toFixed(1)},${yOf(v).toFixed(1)}`).join(" ");
  const base = padT + plotH;
  const area = `${padL},${base.toFixed(1)} ${pts} ${xOf(n - 1).toFixed(1)},${base.toFixed(1)}`;
  const color = opts.color ?? "var(--gm-blue)";
  const labels = opts.labels ?? [];
  const xl = `<text x="${padL}" y="${H - 8}" class="chart-axis" text-anchor="start">${escapeHtml(labels[0] ?? "")}</text>` +
    `<text x="${W - padR}" y="${H - 8}" class="chart-axis" text-anchor="end">${escapeHtml(labels[n - 1] ?? "")}</text>`;
  const end = `<text x="${(xOf(n - 1) - 4).toFixed(1)}" y="${(yOf(values[n - 1]) - 6).toFixed(1)}" class="chart-end-label" text-anchor="end">${escapeHtml(fmt(values[n - 1] ?? 0))}</text>`;
  return `<svg class="chart" viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet" role="img">${grid}` +
    `<polygon points="${area}" fill="${color}" opacity="0.12"/>` +
    `<polyline points="${pts}" fill="none" stroke="${color}" stroke-width="2.5" stroke-linejoin="round"/>${end}${xl}</svg>`;
}

// Horizontal bar chart. data = [{ label, value, color? }].
function hBarChart(data, opts = {}) {
  const W = opts.w ?? 720, rowH = 26, padT = 8, padB = 8, padL = 152, padR = 44;
  const H = padT + padB + data.length * rowH;
  const plotW = W - padL - padR;
  const max = Math.max(1, ...data.map((d) => d.value));
  const rows = data.map((d, i) => {
    const cy = padT + i * rowH;
    const bw = Math.max(1, (d.value / max) * plotW);
    const isHome = opts.homeLabel && d.label === opts.homeLabel;
    const color = d.color ?? (isHome ? "var(--gm-red)" : "var(--gm-blue)");
    const label = escapeHtml(d.label) + (isHome ? ` <tspan class="chart-home-tag">· home</tspan>` : "");
    return `<text x="${padL - 8}" y="${(cy + rowH / 2 + 3).toFixed(1)}" class="chart-row-label" text-anchor="end">${label}</text>` +
      `<rect x="${padL}" y="${(cy + 4).toFixed(1)}" width="${bw.toFixed(1)}" height="${rowH - 10}" rx="2" fill="${color}"><title>${escapeHtml(d.label)}: ${d.value}</title></rect>` +
      `<text x="${(padL + bw + 6).toFixed(1)}" y="${(cy + rowH / 2 + 3).toFixed(1)}" class="chart-bar-value">${d.value}</text>`;
  }).join("");
  return `<svg class="chart" viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet" role="img">${rows}</svg>`;
}

// Donut chart with side legend. data = [{ label, value, color }].
function donutChart(data, total, unitLabel = "") {
  const W = 360, H = 200, cx = 96, cy = 100, R = 78, r = 46;
  let a0 = -90;
  const arcs = data.map((d) => {
    const a1 = a0 + (d.value / total) * 360;
    const path = donutArc(cx, cy, R, r, a0, a1);
    a0 = a1;
    return `<path d="${path}" fill="${d.color}"><title>${escapeHtml(d.label)}: ${d.value} (${Math.round((d.value / total) * 100)}%)</title></path>`;
  }).join("");
  const legend = data.map((d, i) =>
    `<g transform="translate(206, ${24 + i * 24})"><rect width="12" height="12" rx="2" fill="${d.color}"/>` +
    `<text x="18" y="10" class="chart-legend">${escapeHtml(d.label)} · ${d.value}</text></g>`).join("");
  return `<svg class="chart chart-donut" viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet" role="img">${arcs}` +
    `<text x="${cx}" y="${cy - 2}" class="donut-center-num" text-anchor="middle">${total}</text>` +
    `<text x="${cx}" y="${cy + 15}" class="donut-center-label" text-anchor="middle">${escapeHtml(unitLabel)}</text>${legend}</svg>`;
}

function donutArc(cx, cy, R, r, a0, a1) {
  const at = (ang, rad) => {
    const a = (ang * Math.PI) / 180;
    return [cx + rad * Math.cos(a), cy + rad * Math.sin(a)];
  };
  const laf = a1 - a0 > 180 ? 1 : 0;
  const [ox0, oy0] = at(a0, R), [ox1, oy1] = at(a1, R);
  const [ix1, iy1] = at(a1, r), [ix0, iy0] = at(a0, r);
  return `M ${ox0.toFixed(2)} ${oy0.toFixed(2)} A ${R} ${R} 0 ${laf} 1 ${ox1.toFixed(2)} ${oy1.toFixed(2)} ` +
    `L ${ix1.toFixed(2)} ${iy1.toFixed(2)} A ${r} ${r} 0 ${laf} 0 ${ix0.toFixed(2)} ${iy0.toFixed(2)} Z`;
}

// ---- Chart expand modal (lightbox) + PNG/SVG export ----
let modalCharts = null;
let modalChartIndex = null;
let modalTrigger = null;
let chartModalBound = false;

function setupChartModal() {
  if (chartModalBound) return;
  const modal = document.getElementById("chart-modal");
  if (!modal) return;
  chartModalBound = true;
  document.getElementById("chart-modal-close").addEventListener("click", closeChartModal);
  modal.addEventListener("click", (ev) => { if (ev.target === modal) closeChartModal(); });
  document.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape" && !modal.hidden) closeChartModal();
  });
  document.getElementById("chart-dl-png").addEventListener("click", downloadChartPng);
  document.getElementById("chart-dl-svg").addEventListener("click", downloadChartSvg);
  let t;
  window.addEventListener("resize", () => {
    if (modal.hidden) return;
    clearTimeout(t);
    t = setTimeout(renderModalChart, 150);
  });
}

function openChartModal(i) {
  if (!modalCharts || !modalCharts[i]) return;
  const modal = document.getElementById("chart-modal");
  modalChartIndex = i;
  modalTrigger = document.activeElement; // restore focus here on close
  document.getElementById("chart-modal-title").textContent = modalCharts[i].title;
  modal.hidden = false;
  document.body.style.overflow = "hidden"; // lock background scroll
  renderModalChart();
  document.getElementById("chart-modal-close").focus();
}

function renderModalChart() {
  if (modalChartIndex == null) return;
  const body = document.getElementById("chart-modal-body");
  const c = modalCharts[modalChartIndex];
  // Render at a generous width so the exported PNG is slide-grade even on small
  // screens; CSS fits the SVG to the modal (preserveAspectRatio). Time-series
  // charts use a 16:9 height; horizontal bars / donut keep their natural aspect.
  const w = Math.max(Math.round(body.clientWidth), 960);
  const h = c.wide ? Math.round((w * 9) / 16) : undefined;
  body.innerHTML = c.draw(w, h);
}

function closeChartModal() {
  const modal = document.getElementById("chart-modal");
  modal.hidden = true;
  document.body.style.overflow = "";
  document.getElementById("chart-modal-body").innerHTML = "";
  modalChartIndex = null;
  if (modalTrigger && modalTrigger.focus) modalTrigger.focus();
}

// The live chart SVG is styled via CSS classes + CSS variables, neither of which
// survives serialization into a detached SVG (var(--gm-blue) etc. won't resolve,
// so colors/text would drop to defaults). So we clone it and copy each node's
// *computed* style — which has already resolved vars and class rules to literal
// values — onto inline style attributes, making the SVG fully self-contained.
const EXPORT_STYLE_PROPS = [
  "fill", "stroke", "stroke-width", "stroke-linejoin",
  "opacity", "font-family", "font-size", "font-weight",
];
function inlineComputedStyles(src, clone) {
  const cs = getComputedStyle(src);
  let style = clone.getAttribute("style") || "";
  for (const p of EXPORT_STYLE_PROPS) {
    const v = cs.getPropertyValue(p);
    if (v) style += `${p}:${v};`;
  }
  clone.setAttribute("style", style);
  for (let i = 0; i < src.children.length; i++) {
    inlineComputedStyles(src.children[i], clone.children[i]);
  }
}
function selfContainedSvgClone(liveSvg) {
  const clone = liveSvg.cloneNode(true);
  inlineComputedStyles(liveSvg, clone);
  clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  return clone;
}
function chartFileName(ext) {
  const title = modalCharts?.[modalChartIndex]?.title ?? "chart";
  const slug = title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  return `${slug || "chart"}.${ext}`;
}
function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function downloadChartSvg() {
  const live = document.querySelector("#chart-modal-body svg");
  if (!live) return;
  const xml = new XMLSerializer().serializeToString(selfContainedSvgClone(live));
  downloadBlob(new Blob([xml], { type: "image/svg+xml;charset=utf-8" }), chartFileName("svg"));
}
function downloadChartPng() {
  const live = document.querySelector("#chart-modal-body svg");
  if (!live) return;
  const vb = (live.getAttribute("viewBox") || "0 0 960 540").split(/\s+/).map(Number);
  const scale = 2; // 2x for crisp slide use
  const W = Math.round(vb[2] * scale), H = Math.round(vb[3] * scale);
  const clone = selfContainedSvgClone(live);
  clone.setAttribute("width", W);
  clone.setAttribute("height", H);
  const xml = new XMLSerializer().serializeToString(clone);
  const img = new Image();
  img.onload = () => {
    const canvas = document.createElement("canvas");
    canvas.width = W;
    canvas.height = H;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "#ffffff"; // white background so the PNG embeds on any slide
    ctx.fillRect(0, 0, W, H);
    ctx.drawImage(img, 0, 0, W, H);
    canvas.toBlob((blob) => { if (blob) downloadBlob(blob, chartFileName("png")); }, "image/png");
  };
  img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(xml);
}

init();
