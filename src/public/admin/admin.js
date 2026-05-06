// Sabby admin — login, location push, moderation queue.

const $ = (id) => document.getElementById(id);

async function init() {
  const me = await fetch("/admin/me").then((r) => r.json());
  if (me.admin) showDashboard();
  else showLogin();

  $("login-form").addEventListener("submit", onLogin);
  $("logout").addEventListener("click", onLogout);
  $("ping-button").addEventListener("click", onPushLocation);
  document.querySelectorAll(".tabs-row .tab-btn").forEach((btn) =>
    btn.addEventListener("click", () => switchReviewedTab(btn.dataset.status)),
  );
}

function showLogin() {
  $("login-card").hidden = false;
  $("dashboard").hidden = true;
  $("logout").hidden = true;
  $("token").focus();
}

async function showDashboard() {
  $("login-card").hidden = true;
  $("dashboard").hidden = false;
  $("logout").hidden = false;
  await refreshPending();
  await switchReviewedTab("approved");
}

async function onLogin(ev) {
  ev.preventDefault();
  const token = $("token").value;
  const errEl = $("login-error");
  errEl.hidden = true;
  const r = await fetch("/admin/login", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ token }),
  });
  if (r.ok) {
    $("token").value = "";
    showDashboard();
  } else if (r.status === 429) {
    errEl.textContent = "Too many attempts — wait a minute.";
    errEl.hidden = false;
  } else {
    errEl.textContent = "Wrong token.";
    errEl.hidden = false;
  }
}

async function onLogout() {
  await fetch("/admin/logout", { method: "POST" });
  showLogin();
}

async function onPushLocation() {
  const btn = $("ping-button");
  const status = $("ping-status");
  status.textContent = "Asking the browser for your location…";
  btn.disabled = true;
  if (!navigator.geolocation) {
    status.textContent = "This browser doesn't support geolocation.";
    btn.disabled = false;
    return;
  }
  navigator.geolocation.getCurrentPosition(async (pos) => {
    const label = $("ping-label").value.trim();
    const r = await fetch("/api/location", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        lat: pos.coords.latitude,
        lng: pos.coords.longitude,
        label: label || undefined,
      }),
    });
    if (r.ok) {
      const j = await r.json();
      status.innerHTML = `<span class="success">Pushed.</span> ${j.ping.lat.toFixed(4)}, ${j.ping.lng.toFixed(4)} at ${new Date(j.ping.ts).toLocaleTimeString()}`;
      $("ping-label").value = "";
    } else if (r.status === 401) {
      status.textContent = "Session expired. Sign in again.";
      showLogin();
    } else {
      status.textContent = "Push failed: " + r.status;
    }
    btn.disabled = false;
  }, (err) => {
    status.textContent = "Geolocation error: " + err.message;
    btn.disabled = false;
  }, { enableHighAccuracy: true, timeout: 15_000 });
}

async function refreshPending() {
  const r = await fetch("/api/submissions?status=pending");
  if (r.status === 401) { showLogin(); return; }
  const j = await r.json();
  const list = $("pending-list");
  list.innerHTML = "";
  $("pending-empty").hidden = j.submissions.length > 0;
  for (const s of j.submissions) list.appendChild(renderPending(s));
}

function renderPending(s) {
  const el = document.createElement("div");
  el.className = "sub";
  el.innerHTML = `
    <div class="sub-head">
      <div>
        <div class="sub-name"></div>
        <div class="sub-meta"></div>
      </div>
    </div>
    <div class="sub-body"></div>
    <a class="sub-link" target="_blank" rel="noopener noreferrer" hidden></a>
    <div class="sub-actions">
      <textarea placeholder="Reviewer note (optional, internal)"></textarea>
      <button class="btn btn-approve">Approve</button>
      <button class="btn btn-ghost btn-reject">Reject</button>
    </div>
  `;
  el.querySelector(".sub-name").textContent = s.name;
  el.querySelector(".sub-meta").textContent = formatMeta(s);
  el.querySelector(".sub-body").textContent = s.description ?? "";
  const link = el.querySelector(".sub-link");
  if (s.url) { link.href = s.url; link.textContent = s.url; link.hidden = false; }
  const note = el.querySelector("textarea");
  el.querySelector(".btn-approve").addEventListener("click", () => moderate(s.id, "approve", note.value, el));
  el.querySelector(".btn-reject").addEventListener("click", () => moderate(s.id, "reject", note.value, el));
  return el;
}

function formatMeta(s) {
  const bits = [];
  if (s.for_date) bits.push(s.for_date);
  if (s.for_stop) bits.push(s.for_stop);
  if (s.submitter_name) bits.push(`by ${s.submitter_name}`);
  bits.push(`#${s.id}`);
  return bits.join(" · ");
}

async function moderate(id, action, note, el) {
  el.querySelectorAll("button").forEach((b) => (b.disabled = true));
  const r = await fetch(`/admin/submissions/${id}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ action, note: note || undefined }),
  });
  if (r.ok) {
    el.style.opacity = "0.4";
    setTimeout(refreshPending, 250);
    setTimeout(() => switchReviewedTab(currentReviewedStatus()), 300);
  } else {
    el.querySelectorAll("button").forEach((b) => (b.disabled = false));
    alert("Failed: " + r.status);
  }
}

let currentReviewed = "approved";
function currentReviewedStatus() { return currentReviewed; }

async function switchReviewedTab(status) {
  currentReviewed = status;
  document.querySelectorAll(".tabs-row .tab-btn").forEach((btn) =>
    btn.classList.toggle("active", btn.dataset.status === status),
  );
  const r = await fetch(`/api/submissions?status=${status}`);
  if (r.status === 401) { showLogin(); return; }
  const j = await r.json();
  const list = $("reviewed-list");
  list.innerHTML = "";
  if (j.submissions.length === 0) {
    list.innerHTML = `<div class="muted">Nothing here.</div>`;
    return;
  }
  for (const s of j.submissions) list.appendChild(renderReviewed(s));
}

function renderReviewed(s) {
  const el = document.createElement("div");
  el.className = "sub";
  el.innerHTML = `
    <div class="sub-head">
      <div>
        <div class="sub-name"></div>
        <div class="sub-meta"></div>
      </div>
      <span class="pill"></span>
    </div>
    <div class="sub-body"></div>
    <div class="sub-link-wrap"></div>
    <div class="sub-meta reviewer-note" hidden></div>
  `;
  el.querySelector(".sub-name").textContent = s.name;
  el.querySelector(".sub-meta").textContent = formatMeta(s);
  el.querySelector(".sub-body").textContent = s.description ?? "";
  const pill = el.querySelector(".pill");
  pill.textContent = s.status;
  pill.classList.add(s.status);
  if (s.url) {
    const a = document.createElement("a");
    a.className = "sub-link"; a.href = s.url; a.target = "_blank"; a.rel = "noopener noreferrer";
    a.textContent = s.url;
    el.querySelector(".sub-link-wrap").appendChild(a);
  }
  if (s.reviewer_note) {
    const n = el.querySelector(".reviewer-note");
    n.textContent = `Note: ${s.reviewer_note}`;
    n.hidden = false;
  }
  return el;
}

init();
