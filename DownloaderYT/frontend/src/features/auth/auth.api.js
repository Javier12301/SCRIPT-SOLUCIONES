import { api } from "../../services/api.js";

export async function login(payload) {
  const { data } = await api.post("/api/auth/login", payload);
  return data;
}

export async function logout() {
  const { data } = await api.post("/api/auth/logout");
  return data;
}

export async function getMe() {
  const { data } = await api.get("/api/auth/me");
  return data;
}

export async function registerUser(payload) {
  const { data } = await api.post("/api/auth/register", payload);
  return data;
}
