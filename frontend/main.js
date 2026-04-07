/**
 * NetShield IDS — Real-Time Intrusion Detection Dashboard
 *
 * Main application logic for the live attack visualization dashboard.
 * Handles WebSocket connections, map markers, event feed, and stats polling.
 *
 * @version 1.0.0
 * @license MIT
 */

/* ════════════════════════════════════════════════════════════════════
   MAP INITIALIZATION
   ════════════════════════════════════════════════════════════════════ */

const map = L.map("map", {
  center: [20, 0],
  zoom: 2,
  minZoom: 2,
  maxZoom: 18,
  zoomControl: true,
  attributionControl: true,
});

L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
}).addTo(map);

/* ════════════════════════════════════════════════════════════════════
   DOM REFERENCES
   ════════════════════════════════════════════════════════════════════ */

const statusDot = document.getElementById("status-dot");
const statusText = document.getElementById("status-text");
const eventListEl = document.getElementById("event-list");
const feedEmpty = document.getElementById("feed-empty");
const clockEl = document.getElementById("clock");
const btnAutoScroll = document.getElementById("btn-auto-scroll");
const btnClearFeed = document.getElementById("btn-clear-feed");

// Stats elements
const totalAlertsEl = document.getElementById("total-alerts");
const uniqueSourcesEl = document.getElementById("unique-sources");
const totalObservationsEl = document.getElementById("total-observations");
const threatLevelEl = document.getElementById("threat-level");
const threatCard = document.getElementById("stat-threat");

/* ════════════════════════════════════════════════════════════════════
   STATE
   ════════════════════════════════════════════════════════════════════ */

const markersByIp = new Map();
let autoScroll = true;
let eventCount = 0;
let uniqueSources = new Set();

/* ════════════════════════════════════════════════════════════════════
   CLASSIFICATION UTILITIES
   ════════════════════════════════════════════════════════════════════ */

const CLASSIFICATION_MAP = {
  SYN_FLOOD:  { css: "syn-flood",  marker: "marker-syn",  label: "SYN Flood" },
  UDP_FLOOD:  { css: "udp-flood",  marker: "marker-udp",  label: "UDP Flood" },
  ICMP_FLOOD: { css: "icmp-flood", marker: "marker-icmp", label: "ICMP Flood" },
  VOLUMETRIC: { css: "volumetric", marker: "marker-vol",  label: "Volumetric" },
};

function getClassInfo(classification) {
  return CLASSIFICATION_MAP[classification] || CLASSIFICATION_MAP.VOLUMETRIC;
}

/* ════════════════════════════════════════════════════════════════════
   CLOCK
   ════════════════════════════════════════════════════════════════════ */

function updateClock() {
  const now = new Date();
  clockEl.textContent = now.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}
updateClock();
setInterval(updateClock, 1000);

/* ════════════════════════════════════════════════════════════════════
   CONNECTION STATUS
   ════════════════════════════════════════════════════════════════════ */

function setConnectionStatus(state, text) {
  statusDot.className = "status-dot " + state;
  statusText.textContent = text;
}

/* ════════════════════════════════════════════════════════════════════
   MAP MARKERS
   ════════════════════════════════════════════════════════════════════ */

function createMarkerIcon(classification) {
  const info = getClassInfo(classification);
  return L.divIcon({
    className: "",
    html: `<div class="custom-marker ${info.marker}"><div class="marker-ring"></div></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
    popupAnchor: [0, -10],
  });
}

function upsertMarker(event) {
  const lat = event.location?.latitude;
  const lon = event.location?.longitude;
  if (lat == null || lon == null) return;

  const info = getClassInfo(event.classification);
  const popup = `
    <div style="font-family: var(--font-sans); min-width: 180px;">
      <div style="font-weight: 600; margin-bottom: 4px; color: var(--accent);">
        ${info.label}
      </div>
      <div style="font-family: var(--font-mono); font-size: 0.75rem; margin-bottom: 6px;">
        ${event.source_ip} → ${event.destination_ip ?? "—"}
      </div>
      <div style="font-size: 0.7rem; color: var(--text-secondary);">
        ${event.location?.country ?? "Unknown"}${event.location?.city ? ", " + event.location.city : ""}
      </div>
      <div style="font-size: 0.7rem; color: var(--text-muted); margin-top: 2px;">
        ${event.packet_count_window} packets in window
      </div>
    </div>
  `;

  const icon = createMarkerIcon(event.classification);

  if (markersByIp.has(event.source_ip)) {
    const marker = markersByIp.get(event.source_ip);
    marker.setLatLng([lat, lon]);
    marker.setIcon(icon);
    marker.setPopupContent(popup);
  } else {
    const marker = L.marker([lat, lon], { icon }).addTo(map).bindPopup(popup);
    markersByIp.set(event.source_ip, marker);
  }
}

/* ════════════════════════════════════════════════════════════════════
   EVENT FEED
   ════════════════════════════════════════════════════════════════════ */

function addEventToFeed(event) {
  // Hide empty state
  if (!feedEmpty.classList.contains("hidden")) {
    feedEmpty.classList.add("hidden");
  }

  const info = getClassInfo(event.classification);
  const locationText = event.location?.country
    ? `${event.location.country}${event.location.city ? ", " + event.location.city : ""}`
    : "Unknown location";

  const item = document.createElement("li");
  item.className = info.css;
  item.innerHTML = `
    <div class="event-header">
      <span class="event-ip">${event.source_ip} → ${event.destination_ip ?? "—"}</span>
      <span class="event-time">${new Date(event.timestamp).toLocaleTimeString("en-US", { hour12: false })}</span>
    </div>
    <div class="event-meta">
      <span class="pill ${info.css}">${info.label}</span>
      <span>${locationText}</span>
      <span>${event.packet_count_window} pkts</span>
    </div>
  `;

  eventListEl.prepend(item);

  // Limit feed size
  while (eventListEl.children.length > CONFIG.MAX_FEED_ITEMS) {
    eventListEl.removeChild(eventListEl.lastChild);
  }

  // Update local counters
  eventCount++;
  uniqueSources.add(event.source_ip);

  // Auto-scroll
  if (autoScroll) {
    eventListEl.scrollTop = 0;
  }
}

/* ════════════════════════════════════════════════════════════════════
   STATS POLLING
   ════════════════════════════════════════════════════════════════════ */

function formatNumber(n) {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1) + "K";
  return String(n);
}

async function pollStats() {
  try {
    const res = await fetch(CONFIG.API_STATS);
    if (!res.ok) return;
    const data = await res.json();

    totalAlertsEl.textContent = formatNumber(data.total_alerts ?? eventCount);
    uniqueSourcesEl.textContent = formatNumber(data.unique_sources ?? uniqueSources.size);
    totalObservationsEl.textContent = formatNumber(data.total_observations ?? 0);

    const level = data.threat_level ?? "NONE";
    threatLevelEl.textContent = level;
    threatLevelEl.setAttribute("data-level", level);
    threatCard.setAttribute("data-level", level);
  } catch {
    // Use local counters as fallback
    totalAlertsEl.textContent = formatNumber(eventCount);
    uniqueSourcesEl.textContent = formatNumber(uniqueSources.size);
  }
}

setInterval(pollStats, CONFIG.STATS_POLL_INTERVAL);

/* ════════════════════════════════════════════════════════════════════
   INITIAL DATA LOAD
   ════════════════════════════════════════════════════════════════════ */

async function loadRecentEvents() {
  try {
    const response = await fetch(CONFIG.API_EVENTS);
    if (!response.ok) return;
    const events = await response.json();

    events.forEach((event) => {
      upsertMarker(event);
      addEventToFeed(event);
    });

    // Initial stats fetch
    await pollStats();
  } catch {
    setConnectionStatus("error", "Failed to load recent events");
  }
}

/* ════════════════════════════════════════════════════════════════════
   WEBSOCKET CONNECTION
   ════════════════════════════════════════════════════════════════════ */

function connectSocket() {
  const socket = new WebSocket(CONFIG.WS_EVENTS);

  socket.onopen = () => {
    setConnectionStatus("connected", "Monitoring live traffic");
  };

  socket.onmessage = (message) => {
    try {
      const event = JSON.parse(message.data);
      upsertMarker(event);
      addEventToFeed(event);
    } catch (e) {
      console.error("Failed to parse WebSocket message:", e);
    }
  };

  socket.onerror = () => {
    setConnectionStatus("error", "Connection error");
  };

  socket.onclose = () => {
    setConnectionStatus("", "Reconnecting…");
    setTimeout(connectSocket, CONFIG.RECONNECT_DELAY);
  };
}

/* ════════════════════════════════════════════════════════════════════
   UI EVENT HANDLERS
   ════════════════════════════════════════════════════════════════════ */

// Auto-scroll toggle
btnAutoScroll.classList.add("active");
btnAutoScroll.addEventListener("click", () => {
  autoScroll = !autoScroll;
  btnAutoScroll.classList.toggle("active", autoScroll);
});

// Clear feed
btnClearFeed.addEventListener("click", () => {
  eventListEl.innerHTML = "";
  feedEmpty.classList.remove("hidden");
});

/* ════════════════════════════════════════════════════════════════════
   BOOT
   ════════════════════════════════════════════════════════════════════ */

loadRecentEvents();
connectSocket();
