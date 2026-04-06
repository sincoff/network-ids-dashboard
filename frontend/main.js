const map = L.map("map").setView([20, 0], 2);
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

const statusEl = document.getElementById("status");
const eventListEl = document.getElementById("event-list");
const MAX_FEED_ITEMS = 100;

const markersByIp = new Map();

function addEventToFeed(event) {
  const item = document.createElement("li");
  const locationText = event.location?.country
    ? `${event.location.country}${event.location.city ? `, ${event.location.city}` : ""}`
    : "Unknown location";

  item.innerHTML = `
    <div><strong>${event.source_ip}</strong> -> ${event.destination_ip ?? "unknown destination"}</div>
    <div>${new Date(event.timestamp).toLocaleTimeString()} | ${locationText}</div>
    <span class="pill">${event.classification} (${event.packet_count_window} pkts/window)</span>
  `;
  eventListEl.prepend(item);

  while (eventListEl.children.length > MAX_FEED_ITEMS) {
    eventListEl.removeChild(eventListEl.lastChild);
  }
}

function upsertMarker(event) {
  const lat = event.location?.latitude;
  const lon = event.location?.longitude;
  if (lat == null || lon == null) {
    return;
  }

  const popup = `
    <strong>${event.classification}</strong><br/>
    Source: ${event.source_ip}<br/>
    Destination: ${event.destination_ip ?? "unknown"}<br/>
    Packets in window: ${event.packet_count_window}
  `;

  if (markersByIp.has(event.source_ip)) {
    markersByIp.get(event.source_ip).setLatLng([lat, lon]).setPopupContent(popup);
  } else {
    const marker = L.marker([lat, lon]).addTo(map).bindPopup(popup);
    markersByIp.set(event.source_ip, marker);
  }
}

async function loadRecentEvents() {
  const response = await fetch("/api/events/recent");
  const events = await response.json();
  events.forEach((event) => {
    upsertMarker(event);
    addEventToFeed(event);
  });
}

function connectSocket() {
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${protocol}://${window.location.host}/ws/events`);

  socket.onopen = () => {
    statusEl.textContent = "Connected - monitoring live traffic";
  };

  socket.onmessage = (message) => {
    const event = JSON.parse(message.data);
    upsertMarker(event);
    addEventToFeed(event);
  };

  socket.onerror = () => {
    statusEl.textContent = "Connection error - retrying";
  };

  socket.onclose = () => {
    statusEl.textContent = "Disconnected - retrying in 3s";
    setTimeout(connectSocket, 3000);
  };
}

loadRecentEvents().catch(() => {
  statusEl.textContent = "Failed to fetch recent events";
});
connectSocket();
