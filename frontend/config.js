/**
 * Network IDS Dashboard — Runtime Configuration
 *
 * When hosted on Vercel (frontend-only), set VITE_BACKEND_URL to
 * the VM's public address. When served by the Python backend directly,
 * the default same-origin config works automatically.
 *
 * Usage in Vercel:
 *   Set the environment variable VITE_BACKEND_URL in Vercel project settings
 *   e.g. VITE_BACKEND_URL=http://192.168.182.138:8000
 */

const CONFIG = (() => {
  // Check for injected Vercel environment variable via meta tag
  const meta = document.querySelector('meta[name="backend-url"]');
  const backendUrl = meta?.content || "";

  // If no backend URL is configured, use same-origin (local dev / VM direct)
  const apiBase = backendUrl || window.location.origin;
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
