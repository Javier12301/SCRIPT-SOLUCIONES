export const adminUsers = [
  { id: 1, name: "Maria Lopez", email: "maria.lopez@email.com", status: "Activo", daily: 20, batch: 10, language: "Espanol (ES)", activity: "Hoy, 10:24", tone: "orange" },
  { id: 2, name: "Juan Perez", email: "juan.perez@email.com", status: "Activo", daily: 15, batch: 8, language: "Espanol (ES)", activity: "Hoy, 09:15", tone: "blue" },
  { id: 3, name: "Carla Gomez", email: "carla.gomez@email.com", status: "Activo", daily: 10, batch: 6, language: "Espanol (ES)", activity: "Ayer, 18:03", tone: "purple" },
  { id: 4, name: "Andres Lopez", email: "andres.lopez@email.com", status: "Suspendido", daily: 15, batch: 8, language: "Espanol (ES)", activity: "Hace 2 dias", tone: "green" },
  { id: 5, name: "Valeria Martinez", email: "valeria.martinez@email.com", status: "Activo", daily: 20, batch: 10, language: "Ingles (US)", activity: "Ayer, 12:40", tone: "yellow" },
];

export const adminActivity = [
  { user: "Maria Lopez", action: "Descarga completada", detail: "Aventuras en la Naturaleza.mp4", date: "Hoy, 10:24", kind: "success" },
  { user: "Juan Perez", action: "Descarga fallida", detail: "Receta facil de pasta.mp4", date: "Hoy, 09:45", kind: "danger" },
  { user: "Carla Gomez", action: "Inicio de sesion", detail: "Desde Chrome - Windows", date: "Hoy, 09:12", kind: "info" },
  { user: "Andres Lopez", action: "Cuenta suspendida", detail: "Por limite excedido", date: "Ayer, 22:18", kind: "warning" },
];
