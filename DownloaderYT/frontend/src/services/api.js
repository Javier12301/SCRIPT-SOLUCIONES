import axios from "axios";

export const API_BASE_URL = import.meta.env.VITE_API_URL || "";

export const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

export function getApiErrorMessage(error, fallback = "No se pudo completar la accion") {
  return error?.response?.data?.detail || error?.response?.data?.message || error?.message || fallback;
}
