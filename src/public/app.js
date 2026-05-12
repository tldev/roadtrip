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
  setActiveView("day");
  // Render the day card *after* the view is unhidden so Leaflet measures
  // the day-map container correctly. Otherwise the map initializes inside
  // a hidden (display:none) element and renders broken on first load.
  renderSelectedDay();

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
    tab.addEventListener("click", () => setActiveView(tab.dataset.view));
  });
}

function setActiveView(view) {
  document.querySelectorAll(".tab").forEach((t) =>
    t.setAttribute("aria-selected", String(t.dataset.view === view)),
  );
  document.querySelectorAll(".view").forEach((v) => (v.hidden = v.id !== `view-${view}`));
  if (view === "trip") {
    if (!mapDrawn) drawTripMap();
    setTimeout(() => mapInstance?.invalidateSize(), 50);
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
  const dayPct = (dayN / totalDays) * 100;
  const milesSoFar = milesThroughDay(dayIdx);
  const milePct = totalMiles > 0 ? (milesSoFar / totalMiles) * 100 : 0;
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

init();
