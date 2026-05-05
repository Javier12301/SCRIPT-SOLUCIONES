# Backend Falta Implementar - Soporte Para Frontend Planificado

## 1. Objetivo

Registrar las brechas entre el backend actual de DownloaderYT V1.1 y las pantallas planificadas para el frontend.

Este documento evita que el frontend invente datos como si fueran reales. Las funciones no soportadas por API se podran mostrar como mock, deshabilitadas o preparadas para conexion futura.

## 2. Backend Actual Disponible

Segun `docs/frontend_endpoints.md`, ya existen:

### Auth

- `POST /api/auth/login`
- `POST /api/auth/logout`
- `POST /api/auth/register`
- `GET /api/auth/me`

### Jobs

- `POST /api/jobs`
- `GET /api/jobs`
- `GET /api/jobs/{job_id}`
- `POST /api/jobs/{job_id}/cancel`

### Items

- `POST /api/items/{item_id}/retry`
- `GET /api/items/{item_id}/download`

### Eventos

- `GET /api/events`

### Admin

- `POST /api/admin/update-extractor`

## 3. Brechas Principales Frente A Los Disenos

Los mockups incluyen capacidades que aun no tienen endpoint o modelo suficiente:

- Gestion completa de usuarios desde admin.
- Edicion de limites por usuario.
- Suspender/activar usuarios.
- Politicas globales del sistema.
- Metricas administrativas reales.
- Actividad reciente global.
- Cuota diaria restante.
- Almacenamiento usado.
- Notificaciones.
- Preferencias de idioma persistentes.
- Integraciones Google Drive y WhatsApp.

## 4. Usuarios Admin

### 4.1 Listar Usuarios

Falta endpoint:

```txt
GET /api/admin/users
```

Respuesta propuesta:

```json
{
  "users": [
    {
      "id": 1,
      "username": "maria",
      "email": "maria@example.com",
      "role": "user",
      "status": "active",
      "language": "es-ES",
      "daily_download_limit": 20,
      "batch_url_limit": 10,
      "created_at": "2026-05-05T10:00:00",
      "last_seen_at": "2026-05-05T11:00:00"
    }
  ]
}
```

Campos/modelo faltantes:

- `email`
- `status`: `active|suspended|invited`
- `language`
- `daily_download_limit`
- `batch_url_limit`
- `last_seen_at` expuesto por usuario

### 4.2 Crear Usuario Con Mas Campos

Existe:

```txt
POST /api/auth/register
```

Actualmente recibe:

```json
{
  "username": "nuevo_usuario",
  "password": "password_seguro"
}
```

Faltaria soportar opcionalmente:

```json
{
  "username": "nuevo_usuario",
  "password": "password_seguro",
  "email": "nuevo@example.com",
  "language": "es-ES",
  "daily_download_limit": 20,
  "batch_url_limit": 10,
  "role": "user"
}
```

### 4.3 Editar Usuario

Falta endpoint:

```txt
PATCH /api/admin/users/{user_id}
```

Payload propuesto:

```json
{
  "email": "nuevo@example.com",
  "language": "es-ES",
  "daily_download_limit": 20,
  "batch_url_limit": 10,
  "role": "user"
}
```

Reglas:

- Solo admin.
- No permitir que admin se quite su propio rol si queda sin otro admin.
- Validar limites positivos.

### 4.4 Suspender Y Activar Usuario

Faltan endpoints:

```txt
POST /api/admin/users/{user_id}/suspend
POST /api/admin/users/{user_id}/activate
```

Comportamiento esperado:

- Usuario suspendido no puede iniciar sesion.
- Al suspender, revocar sesiones activas.
- No permitir suspender el ultimo admin activo.

## 5. Politicas Del Sistema

Los mockups muestran politicas globales:

- Limite de descargas por dia.
- Limite de URLs por lote.
- Idioma predeterminado.
- Formatos permitidos.
- Mostrar Google Drive.
- Mostrar WhatsApp.

Falta endpoint:

```txt
GET /api/admin/policies
PUT /api/admin/policies
```

Respuesta propuesta:

```json
{
  "daily_download_limit": 20,
  "batch_url_limit": 10,
  "default_language": "es-ES",
  "allowed_output_profiles": ["video_mp4", "audio_mp3"],
  "google_drive_enabled": false,
  "whatsapp_enabled": false
}
```

Nota:

- Google Drive y WhatsApp estan fuera de alcance V1.1 segun `docs/arquitectura.md` y `PLAN.md`.
- Si se muestran en frontend V1.1, deben figurar como deshabilitados o futuros.

## 6. Metricas Admin

Los mockups muestran:

- Usuarios totales.
- Descargas hoy.
- Descargas completadas.
- Descargas fallidas.
- Almacenamiento usado.

Falta endpoint:

```txt
GET /api/admin/metrics
```

Respuesta propuesta:

```json
{
  "total_users": 28,
  "downloads_today": 152,
  "completed_downloads": 4982,
  "failed_downloads": 37,
  "storage_used_bytes": 275736903680,
  "storage_limit_bytes": 536870912000,
  "trends": {
    "users_month_delta": 4,
    "downloads_today_pct_delta": 18
  }
}
```

Requiere:

- Agregaciones por `users`, `jobs`, `job_items`.
- Calculo de almacenamiento bajo `downloads/` o desde DB si se persiste tamano final.

## 7. Actividad Reciente Admin

Los mockups muestran actividad tipo auditoria:

- Descarga completada.
- Descarga fallida.
- Inicio de sesion.
- Cuenta suspendida.
- Password restablecida.
- Politica actualizada.

Falta modelo y endpoints:

```txt
GET /api/admin/activity
```

Tabla propuesta:

```txt
audit_events
- id
- actor_user_id nullable
- target_user_id nullable
- event_type
- detail_json
- created_at
```

Respuesta propuesta:

```json
{
  "events": [
    {
      "id": 1,
      "actor_username": "admin",
      "target_username": "maria",
      "event_type": "download_completed",
      "label": "Descarga completada",
      "detail": "Aventuras en la Naturaleza.mp4",
      "created_at": "2026-05-05T10:24:00"
    }
  ]
}
```

## 8. Cuotas Y Limites Por Usuario

La UI de usuario muestra:

- Cupo diario restante.
- Limite diario total.

Falta endpoint:

```txt
GET /api/me/usage
```

Respuesta propuesta:

```json
{
  "daily_download_limit": 10,
  "downloads_used_today": 2,
  "downloads_remaining_today": 8,
  "batch_url_limit": 10
}
```

Requiere:

- Definir si la cuota cuenta jobs, items o solo items completados/iniciados.
- Validar cuota en `POST /api/jobs`.
- Responder `409` o `429` si excede limite.

## 9. Settings De Usuario

La arquitectura menciona tabla `settings`, pero los endpoints frontend no documentan gestion de settings.

Faltan endpoints:

```txt
GET /api/settings/me
PUT /api/settings/me
```

Campos utiles:

- `download_root_override`
- `concurrency`
- `auto_transfer_enabled`
- `transfer_target_path`
- `language`
- `theme`

Nota:

- `theme` podria quedarse solo en frontend si no se necesita sincronizacion entre dispositivos.
- `language` conviene persistir en backend si afecta textos, formatos o defaults.

## 10. Descargas Recientes E Historial

Actualmente `GET /api/jobs` permite derivar recientes desde jobs/items.

Opcionalmente se podria agregar:

```txt
GET /api/items/recent
GET /api/items/active
```

Ventajas:

- Menos transformacion en frontend.
- Paginacion mas simple.
- Mejor performance cuando haya muchos jobs.

Respuesta propuesta:

```json
{
  "items": [],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 120
  }
}
```

## 11. Paginacion Y Filtros

Para escalar listas:

Faltaria agregar query params a endpoints existentes o nuevos:

```txt
GET /api/jobs?page=1&page_size=20&status=completed&search=texto
GET /api/admin/users?page=1&page_size=20&status=active&search=maria
GET /api/admin/activity?page=1&page_size=20&type=download_failed
```

## 12. Calidad, Nombre Personalizado Y Rangos

La UI planifica opciones:

- Calidad.
- Nombre personalizado.
- Inicio/fin para recorte.
- Opciones avanzadas.

Actualmente `POST /api/jobs` acepta `config` extensible y usa parcialmente:

- `cookies_path`
- `output_profile`
- `ytdlp_options`

Faltaria definir soporte real para:

```json
{
  "quality": "best",
  "custom_name": "mi-video",
  "trim_start": "00:00:30",
  "trim_end": "00:05:20"
}
```

Requiere:

- Validacion backend.
- Sanitizacion fuerte de nombres.
- Definir si recorte usa ffmpeg postprocesado.
- Manejo de errores si el formato/tiempo no aplica.

## 13. Notificaciones

Los mockups muestran campana con contador.

Faltan endpoints/modelo:

```txt
GET /api/notifications
POST /api/notifications/{notification_id}/read
POST /api/notifications/read-all
```

Tabla propuesta:

```txt
notifications
- id
- user_id
- type
- title
- message
- read_at nullable
- created_at
```

## 14. Almacenamiento Usado

Para admin y usuario se muestra o podria mostrarse almacenamiento.

Faltan:

- Persistir `file_size_bytes` en `job_items` al completar.
- Endpoint admin global: incluido en `GET /api/admin/metrics`.
- Endpoint usuario: podria incluirse en `GET /api/me/usage`.

## 15. Google Drive Y WhatsApp

Segun `docs/arquitectura.md` y `PLAN.md`, Google Drive esta fuera de alcance V1.1. WhatsApp tampoco forma parte del backend actual.

Si se implementan en V2, faltarian:

### Google Drive

- OAuth o credenciales de servicio.
- Asociacion por usuario o global admin.
- Endpoint para subir archivo completado.
- Estado de transferencia y errores.

Endpoints posibles:

```txt
POST /api/items/{item_id}/upload/google-drive
GET /api/integrations/google-drive/status
```

### WhatsApp

- Definir proveedor/API.
- Validar privacidad y limites.
- Envio de link o archivo.

Endpoints posibles:

```txt
POST /api/items/{item_id}/share/whatsapp
GET /api/integrations/whatsapp/status
```

## 16. Seguridad Requerida Para Nuevos Endpoints

- Todo endpoint admin debe usar `require_admin`.
- No exponer existencia de recursos de otros usuarios.
- Mantener ownership estricto.
- Validar payloads con Pydantic.
- Auditar acciones administrativas sensibles.
- Revocar sesiones cuando se suspenda usuario.
- Rate limit en login, register admin y acciones sensibles.

## 17. Prioridad Recomendada

### Alta

- `GET /api/admin/users`
- `PATCH /api/admin/users/{user_id}`
- `POST /api/admin/users/{user_id}/suspend`
- `POST /api/admin/users/{user_id}/activate`
- `GET /api/me/usage`
- Paginacion/filtros para jobs.

### Media

- `GET/PUT /api/admin/policies`
- `GET /api/admin/metrics`
- `GET /api/admin/activity`
- `GET/PUT /api/settings/me`
- Persistir `file_size_bytes`.

### Baja O V2

- Notificaciones completas.
- Google Drive.
- WhatsApp.
- Recorte por rangos.
- Historial separado si `GET /api/jobs` deja de ser suficiente.

## 18. Impacto En Frontend

Hasta que estos endpoints existan:

- Admin users se podra mostrar con mock aislado o solo formulario real de crear usuario.
- Politicas se mostraran como UI preparada, sin persistencia real.
- Actividad reciente sera mock.
- Metricas admin seran derivadas parcialmente de jobs del usuario actual o mock.
- Cuota diaria restante se mostrara mock/deshabilitada.
- Google Drive y WhatsApp se ocultaran o marcaran como futuras.
