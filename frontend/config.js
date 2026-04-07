/**
 * NetShield IDS — Runtime Configuration
 *
 * The dashboard is designed to be hosted locally within the Ubuntu VM
 * and served behind the Nginx reverse proxy, seamlessly using the 
 * underlying same-origin to route API and WebSocket traffic.
 */

const CONFIG = (() => {
  // Use same-origin (served directly by VM's Nginx/FastAPI)
  const apiBase = window.location.origin;
  const wsProtocol = apiBase.startsWith("https") ? "wss" : "ws";
  const wsBase = apiBase.replace(/^https?/, wsProtocol);

  return Object.freeze({
    API_BASE: apiBase,
    WS_BASE: wsBase,
    API_EVENTS: `${apiBase}/api/events/recent`,
    API_STATS: `${apiBase}/api/stats`,
    API_HEALTH: `${apiBase}/api/health`,
    WS_EVENTS: `${wsBase}/ws/events`,
    STATS_POLL_INTERVAL: 3000,
    MAX_FEED_ITEMS: 200,
    RECONNECT_DELAY: 3000,
  });
})();
