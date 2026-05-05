import { api } from "../../services/api.js";

export async function listJobs() {
  const { data } = await api.get("/api/jobs");
  return data;
}

export async function createJob(payload) {
  const { data } = await api.post("/api/jobs", payload);
  return data;
}

export async function cancelJob(jobId) {
  const { data } = await api.post(`/api/jobs/${jobId}/cancel`);
  return data;
}

export async function retryItem(itemId) {
  const { data } = await api.post(`/api/items/${itemId}/retry`);
  return data;
}

export function getDownloadUrl(itemId) {
  const base = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");
  return `${base}/api/items/${itemId}/download`;
}
