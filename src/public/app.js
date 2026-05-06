// Sabby Roadtrip — public site, slice 2
// Daily docket, full-trip map, visitor suggestion form, live ping status, countdown.

const BIOME_THEMES = {
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

let trip, itinerary, geometries, todayPayload, config;
let mapInstance, mapDrawn = false;
let approvedSubmissions = [];
let activeSuggestContext = null;
let captchaWidgetId = null;
let countdownTimer = null;
let pingTimer = null;

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

  renderDayView("today", todayPayload.today, todayPayload.referenceDate);
  renderDayView("tomorrow", todayPayload.tomorrow, nextIso(todayPayload.referenceDate));
  themeForDay(todayPayload.today ?? todayPayload.tomorrow);

  setupTabs();
  setActiveView("today");

  refreshPingStatus();
  pingTimer = setInterval(refreshPingStatus, 60_000);

  loadHCaptchaIfNeeded();
  setupSuggestModal();
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
  if (view === "today") themeForDay(todayPayload.today ?? todayPayload.tomorrow);
  if (view === "tomorrow") themeForDay(todayPayload.tomorrow ?? todayPayload.today);
}

function nextIso(iso) {
  const d = new Date(iso + "T00:00:00Z");
  d.setUTCDate(d.getUTCDate() + 1);
  return d.toISOString().slice(0, 10);
}

function renderDayView(slot, day, fallbackDate) {
  const root = document.getElementById(`view-${slot}`);
  if (!day) {
    root.innerHTML = renderEmptyState(slot);
    if (slot === "today") armCountdown();
    return;
  }
  const driveLabel = day.isRestDay ? "Rest day" : day.drivingHours;
  const subs = approvedSubmissions.filter(
    (s) => s.for_date === day.date || (s.for_date == null && s.for_stop && (s.for_stop === day.start || s.for_stop === day.end)),
  );
  root.innerHTML = `
    <article class="day-card">
      <div class="day-eyebrow"><span class="dot"></span>${escapeHtml(day.day || prettyDate(day.date))}${day.isRestDay ? '<span class="rest-pill">Rest</span>' : ""}</div>
      <h1 class="day-title">${prettyDate(day.date)}</h1>
      <div class="day-route">
        <span>${escapeHtml(day.start || "—")}</span>
        <span class="day-arrow">→</span>
        <span>${escapeHtml(day.end || "—")}</span>
      </div>
      <div class="day-stats">
        <div><div class="stat-label">Driving</div><div class="stat-value">${escapeHtml(driveLabel || "—")}</div></div>
        <div><div class="stat-label">Lodging</div><div class="stat-value">${escapeHtml(formatLodging(day.lodging))}</div></div>
        ${day.daytrip ? `<div><div class="stat-label">Daytrip</div><div class="stat-value">${escapeHtml(day.daytrip)}</div></div>` : ""}
      </div>
      <div class="day-cta">
        <button class="btn-suggest" data-date="${day.date}" data-stop="${escapeHtml(day.end || day.start || "")}">+ Suggest a place</button>
      </div>
      ${renderSuggestions(subs)}
    </article>
  `;
  root.querySelector(".btn-suggest")?.addEventListener("click", (ev) => {
    const b = ev.currentTarget;
    openSuggestModal({ date: b.dataset.date, stop: b.dataset.stop });
  });
}

function renderEmptyState(slot) {
  const startIso = itinerary.days[0].date;
  const endIso = itinerary.days[itinerary.days.length - 1].date;
  if (slot === "today") {
    const days = daysUntil(startIso);
    if (days > 0) {
      return `
        <div class="day-empty">
          <h2 id="countdown-headline">Trip kicks off in ${days} ${days === 1 ? "day" : "days"}</h2>
          <p>${prettyDate(startIso)}.</p>
          <button class="btn-suggest btn-suggest-cta" data-date="" data-stop="">+ Suggest a place</button>
        </div>`;
    }
    return `
      <div class="day-empty">
        <h2>End of the road</h2>
        <p>The trip wrapped on ${prettyDate(endIso)}.</p>
      </div>`;
  }
  return `
    <div class="day-empty">
      <h2>Nothing on tomorrow yet</h2>
      <p>${daysUntil(startIso) > 0 ? `Trip starts ${prettyDate(startIso)}.` : `Trip ended ${prettyDate(endIso)}.`}</p>
    </div>`;
}

function armCountdown() {
  if (countdownTimer) clearInterval(countdownTimer);
  countdownTimer = setInterval(() => {
    const headline = document.getElementById("countdown-headline");
    if (!headline) return;
    const days = daysUntil(itinerary.days[0].date);
    headline.textContent =
      days > 0 ? `Trip kicks off in ${days} ${days === 1 ? "day" : "days"}`
      : "Trip starts today!";
  }, 60_000);
  document.querySelector(".btn-suggest-cta")?.addEventListener("click", () =>
    openSuggestModal({ date: "", stop: "" }),
  );
}

function daysUntil(iso) {
  const start = new Date(iso + "T00:00:00Z").getTime();
  const today = new Date(new Date().toISOString().slice(0, 10) + "T00:00:00Z").getTime();
  return Math.round((start - today) / 86_400_000);
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

function themeForDay(day) {
  const key = LOCATION_BIOME[day?.end] ?? LOCATION_BIOME[day?.start] ?? "gulf";
  const [bg, accent, accent2] = BIOME_THEMES[key];
  document.documentElement.style.setProperty("--theme-bg", bg);
  document.documentElement.style.setProperty("--theme-accent", accent);
  document.documentElement.style.setProperty("--theme-accent-2", accent2);
  document.querySelector('meta[name="theme-color"]').setAttribute("content", bg);
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
    block.innerHTML = `<div class="leg-name">${escapeHtml(leg.name)}</div>`;
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
      marker.bindPopup(`<b>${escapeHtml(stop.name)}</b><br>${escapeHtml(stop.address)}`);

      const row = document.createElement("div");
      row.className = `stop-row ${stop.type}`;
      row.innerHTML = `<span class="stop-bullet"></span><span></span>`;
      row.querySelector("span:nth-child(2)").textContent = stop.name;
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
    m.bindPopup(`<b>${escapeHtml(dt.name)}</b><br>Daytrip near ${escapeHtml(dt.nearStop)}`);
  });

  mapInstance.fitBounds(allCoords, { padding: [40, 40] });
}

function getCss(varName) {
  return getComputedStyle(document.documentElement).getPropertyValue(varName).trim() || "#d18a4a";
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
      theme: "dark",
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
