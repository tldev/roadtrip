// Sabby Roadtrip — public site, slice 1
// Read-only daily docket + full-trip map. Theme shifts by the day's terrain.

const BIOME_THEMES = {
  // [bg, accent, accent-2]
  gulf:        ["#0e1a24", "#5fa3b0", "#d3a35f"],
  hill:        ["#1a1d10", "#c1a14a", "#7a956a"],
  west_desert: ["#231a12", "#d18a4a", "#8e6a55"],
  high_desert: ["#1f1310", "#c87455", "#7da89a"],
  red_rock:    ["#1d100b", "#cf6a3a", "#d6b27a"],
  pacific:     ["#0c1820", "#56a4af", "#e2b97a"],
  mojave:      ["#1a1610", "#d6b27a", "#a26a4a"],
  rockies:     ["#10151f", "#6f9ad6", "#c4d6a8"],
  plains:      ["#1a160c", "#d6b85a", "#7a956a"],
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

let trip, itinerary, geometries, mapInstance, mapDrawn = false;

async function init() {
  [trip, itinerary, geometries] = await Promise.all([
    fetch("/api/trip").then((r) => r.json()),
    fetch("/api/itinerary").then((r) => r.json()),
    fetch("/api/geometries").then((r) => r.json()),
  ]);

  document.getElementById("trip-dates").textContent = trip.dates;

  const today = await fetch("/api/today").then((r) => r.json());
  renderDayView("today", today.today, today.referenceDate);
  renderDayView("tomorrow", today.tomorrow, nextIso(today.referenceDate));
  themeForDay(today.today ?? today.tomorrow);

  setupTabs();
  setActiveView("today");
  refreshPingStatus();
}

async function refreshPingStatus() {
  try {
    const r = await fetch("/api/location");
    const j = await r.json();
    const el = document.getElementById("ping-status");
    if (j.ping?.ts) {
      const mins = Math.max(0, Math.round((Date.now() - new Date(j.ping.ts).getTime()) / 60000));
      el.textContent = `Last ping ${mins} min ago · ${j.ping.label ?? "on the road"}`;
    } else {
      el.textContent = j.message ?? "Last ping unknown";
    }
  } catch {
    /* leave default */
  }
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
  if (view === "trip" && !mapDrawn) drawTripMap();
  if (view === "today") themeForDay(currentDay("today"));
  if (view === "tomorrow") themeForDay(currentDay("tomorrow"));
}

function currentDay(which) {
  const refIso = which === "today"
    ? itinerary.days.find((d) => d.date === todayIso())?.date ?? todayIso()
    : nextIso(todayIso());
  return itinerary.days.find((d) => d.date === refIso) ?? null;
}

function todayIso() { return new Date().toISOString().slice(0, 10); }
function nextIso(iso) {
  const d = new Date(iso + "T00:00:00Z");
  d.setUTCDate(d.getUTCDate() + 1);
  return d.toISOString().slice(0, 10);
}

function renderDayView(slot, day, fallbackDate) {
  const root = document.getElementById(`view-${slot}`);
  if (!day) {
    root.innerHTML = `
      <div class="day-empty">
        <h2>${slot === "today" ? "Trip hasn't started yet" : "End of the road"}</h2>
        <p>${slot === "today"
          ? `Trip kicks off ${prettyDate(itinerary.days[0].date)}.`
          : `Last day of the trip is ${prettyDate(itinerary.days[itinerary.days.length - 1].date)}.`}</p>
      </div>`;
    return;
  }
  const driveLabel = day.isRestDay ? "Rest day" : day.drivingHours;
  root.innerHTML = `
    <article class="day-card">
      <div class="day-eyebrow"><span class="dot"></span>${day.day || prettyDate(day.date)}${day.isRestDay ? '<span class="rest-pill">Rest</span>' : ""}</div>
      <h1 class="day-title">${prettyDate(day.date)}</h1>
      <div class="day-route">
        <span>${day.start || "—"}</span>
        <span class="day-arrow">→</span>
        <span>${day.end || "—"}</span>
      </div>
      <div class="day-stats">
        <div><div class="stat-label">Driving</div><div class="stat-value">${driveLabel || "—"}</div></div>
        <div><div class="stat-label">Lodging</div><div class="stat-value">${escapeHtml(formatLodging(day.lodging))}</div></div>
        ${day.daytrip ? `<div><div class="stat-label">Daytrip</div><div class="stat-value">${escapeHtml(day.daytrip)}</div></div>` : ""}
      </div>
    </article>
  `;
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

function themeForDay(day) {
  const key = LOCATION_BIOME[day?.end] ?? LOCATION_BIOME[day?.start] ?? "gulf";
  const [bg, accent, accent2] = BIOME_THEMES[key];
  document.documentElement.style.setProperty("--theme-bg", bg);
  document.documentElement.style.setProperty("--theme-accent", accent);
  document.documentElement.style.setProperty("--theme-accent-2", accent2);
  document.querySelector('meta[name="theme-color"]').setAttribute("content", bg);
}

function drawTripMap() {
  mapDrawn = true;
  mapInstance = L.map("map", { zoomControl: false }).setView([36, -100], 5);
  L.control.zoom({ position: "topright" }).addTo(mapInstance);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
    attribution: "&copy; OpenStreetMap &copy; CARTO",
    maxZoom: 19,
  }).addTo(mapInstance);

  const allCoords = [];
  const legend = document.getElementById("trip-stops");
  legend.innerHTML = "";
  const accent = getCss("--theme-accent");
  const accent2 = getCss("--theme-accent-2");

  trip.legs.forEach((leg, li) => {
    const block = document.createElement("div");
    block.className = "leg-block";
    block.innerHTML = `<div class="leg-name">${leg.name}</div>`;
    leg.stops.forEach((stop, si) => {
      allCoords.push([stop.lat, stop.lng]);
      const color = stop.type === "start" ? accent2 : stop.type === "end" ? accent : accent;
      const marker = L.circleMarker([stop.lat, stop.lng], {
        radius: stop.type === "start" || stop.type === "end" ? 8 : 6,
        color: "#fff",
        weight: 1.5,
        fillColor: color,
        fillOpacity: 1,
      }).addTo(mapInstance);
      marker.bindPopup(`<b>${stop.name}</b><br>${stop.address}`);

      const row = document.createElement("div");
      row.className = `stop-row ${stop.type}`;
      row.innerHTML = `<span class="stop-bullet"></span><span>${stop.name}</span>`;
      row.addEventListener("click", () => mapInstance.flyTo([stop.lat, stop.lng], 9, { duration: 0.8 }));
      block.appendChild(row);

      if (si < leg.stops.length - 1) {
        const segKey = `${li}-${si}`;
        const next = leg.stops[si + 1];
        const segCoords = geometries.trip?.[segKey] ?? [
          [stop.lat, stop.lng],
          [next.lat, next.lng],
        ];
        L.polyline(segCoords, { color: accent, weight: 3, opacity: 0.85 }).addTo(mapInstance);
      }
    });
    legend.appendChild(block);
  });

  trip.daytrips.forEach((dt) => {
    const m = L.circleMarker([dt.lat, dt.lng], {
      radius: 4, color: accent2, weight: 1, fillColor: accent2, fillOpacity: 0.8,
    }).addTo(mapInstance);
    m.bindPopup(`<b>${dt.name}</b><br>Daytrip near ${dt.nearStop}`);
  });

  mapInstance.fitBounds(allCoords, { padding: [40, 40] });
}

function getCss(varName) {
  return getComputedStyle(document.documentElement).getPropertyValue(varName).trim() || "#d18a4a";
}

init();
