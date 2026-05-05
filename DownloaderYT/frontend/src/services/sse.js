import { API_BASE_URL } from "./api.js";

export function createEventsSource() {
  const base = API_BASE_URL.replace(/\/$/, "");
  const url = `${base}/api/events`;
  return new EventSource(url, { withCredentials: true });
}
