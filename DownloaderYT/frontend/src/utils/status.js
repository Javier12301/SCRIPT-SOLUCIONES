export const STATUS_LABELS = {
  queued: "En cola",
  downloading: "Descargando",
  processing: "Preparando archivo",
  pending_device_online: "Esperando dispositivo",
  transferring: "Transfiriendo",
  completed: "Completado",
  failed: "Error",
  canceled: "Cancelado",
};

export const STATUS_KIND = {
  queued: "info",
  downloading: "info",
  processing: "warning",
  pending_device_online: "purple",
  transferring: "teal",
  completed: "success",
  failed: "danger",
  canceled: "danger",
};

export function getStatusLabel(status) {
  return STATUS_LABELS[status] || status || "Desconocido";
}

export function getStatusKind(status) {
  return STATUS_KIND[status] || "neutral";
}
