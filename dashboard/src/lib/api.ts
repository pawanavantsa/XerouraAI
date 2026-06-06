export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

/** JWT from dashboard login — required for team-scoped APIs. */
export function bearerHeaders(): HeadersInit {
  if (typeof window === "undefined") return {};
  const t = localStorage.getItem("auth_token");
  return t ? { Authorization: `Bearer ${t}` } : {};
}

/** Optional: scope public web chat WebSocket to a team (UUID). */
export const WIDGET_TEAM_ID =
  process.env.NEXT_PUBLIC_WIDGET_TEAM_ID?.trim() || "";
