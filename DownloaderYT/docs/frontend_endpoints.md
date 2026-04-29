# API para Frontend - DownloaderYT

Este documento describe como consumir la API actual desde frontend (Fases 2-4).

Base local:

- `http://127.0.0.1:8000`

Autenticacion:

- Cookie de sesion HTTP-only (el navegador la maneja automaticamente).
- En `fetch`/cliente HTTP usar `credentials: "include"`.

---

## 1) Auth

### POST `/api/auth/login`

Login por usuario y password.

Request:

```json
{
  "username": "admin",
  "password": "admin1234"
}
```

Response `200`:

```json
{
  "message": "login ok",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin",
    "created_at": "2026-04-25T22:33:41.647934"
  },
  "expires_at": "2026-04-26T22:51:19.008323"
}
```

Errores:

- `401`: credenciales invalidas.

---

### POST `/api/auth/logout`

Cierra sesion actual y revoca token en DB.

Response `200`:

```json
{
  "message": "logout ok (admin)"
}
```

---

### POST `/api/auth/register`

Alta de usuario (solo admin autenticado).

Request:

```json
{
  "username": "nuevo_usuario",
  "password": "password_seguro"
}
```

Response `201`:

```json
{
  "message": "user created",
  "user": {
    "id": 2,
    "username": "nuevo_usuario",
    "role": "user",
    "created_at": "2026-04-29T10:00:00.000000"
  }
}
```

Errores:

- `401`: no autenticado.
- `403`: no admin.
- `409`: username duplicado o reservado.
- `422`: validacion de payload.

---

### GET `/api/auth/me`

Obtiene usuario autenticado.

Response `200`:

```json
{
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin",
    "created_at": "2026-04-25T22:33:41.647934"
  }
}
```

Errores:

- `401`: no autenticado.

---

## 2) Jobs

### POST `/api/jobs`

Crea job con una o multiples fuentes. Si una fuente es playlist, el backend expande a multiples `job_items` (uno por video).

Request:

```json
{
  "sources": [
    "https://www.youtube.com/watch?v=...",
    "https://www.youtube.com/playlist?list=..."
  ],
  "config": {
    "cookies_path": "D:/cookies/youtube.txt",
    "output_profile": "video_mp4",
    "ytdlp_options": {
      "extractor_retries": 2
    },
    "future_flag": {
      "enabled": true
    }
  }
}
```

Notas de `config`:

- `config` es extensible (forward-compatible para V2).
- `cookies_path` y `ytdlp_options` ya son usados por backend.
- `output_profile` opcional soportado:
  - `video_mp4`
  - `audio_mp3`
- Para `video_mp4`, backend prioriza formatos nativos compatibles con Windows:
  - `bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]/best`
  - objetivo: minimizar archivos `.mp4` no reproducibles en Windows Media Player sin recodificacion pesada.
- Campos extra se guardan en `config_json` sin romper contrato.

Response `201` (resumen):

```json
{
  "id": 2,
  "user_id": 1,
  "status": "queued",
  "config": {},
  "created_at": "2026-04-29T03:02:13.566236",
  "updated_at": "2026-04-29T03:02:13.566236",
  "items": [
    {
      "id": 2,
      "job_id": 2,
      "source_url": "https://www.youtube.com/watch?v=...",
      "status": "queued",
      "progress_pct": 0,
      "downloaded_bytes": 0,
      "total_bytes": null,
      "speed": null,
      "eta": null,
      "output_path": null,
      "error_message": null,
      "next_retry_at": null,
      "created_at": "2026-04-29T03:02:13.566236",
      "updated_at": "2026-04-29T03:02:13.566236"
    }
  ]
}
```

Errores:

- `401`: no autenticado.
- `422`: payload invalido / sin fuentes resolubles.

---

### GET `/api/jobs`

Lista jobs del usuario autenticado (ownership estricto).

Response `200`:

```json
{
  "jobs": [
    {
      "id": 2,
      "user_id": 1,
      "status": "queued",
      "config": {},
      "created_at": "2026-04-29T03:02:13.566236",
      "updated_at": "2026-04-29T03:02:13.566236",
      "items": []
    }
  ]
}
```

---

### GET `/api/jobs/{job_id}`

Detalle de job + items.

Errores:

- `401`: no autenticado.
- `404`: job inexistente o no pertenece al usuario.

---

### POST `/api/jobs/{job_id}/cancel`

Cancela job e items activos.

Response `200`:

```json
{
  "message": "job canceled",
  "job_id": 2,
  "status": "canceled"
}
```

Comportamiento:

- Marca `cancel_requested` y corta descarga activa de forma cooperativa.
- Estado final esperado del item: `canceled` (no `completed`).

Errores:

- `401`: no autenticado.
- `404`: job inexistente o no pertenece al usuario.

---

## 3) Items

### POST `/api/items/{item_id}/retry`

Reencola item cancelado/fallido.

Estados permitidos:

- `failed`
- `canceled`
- `pending_device_online`

Response `200`:

```json
{
  "message": "item queued for retry",
  "item_id": 2,
  "status": "queued",
  "updated_at": "2026-04-29T03:07:48.078194"
}
```

Errores:

- `401`: no autenticado.
- `404`: item inexistente o no pertenece al usuario.
- `409`: estado no reintentable (ej. `completed`).

---

### GET `/api/items/{item_id}/download`

Descarga archivo final del item.

Requisitos:

- `status == completed`
- `output_path` existente
- ownership del item

Response `200`:

- `application/octet-stream` (archivo)

Errores:

- `401`: no autenticado.
- `404`: item no pertenece al usuario o archivo no existe.
- `409`: item no completado.

---

## 4) SSE

### GET `/api/events`

Canal de eventos en tiempo real por usuario.

`Content-Type`: `text/event-stream`

Eventos actuales:

1. `connected`
2. `message` (payload de item/job)
3. `ping` (keepalive)

Ejemplo stream:

```text
event: connected
data: {"user_id":1}

event: message
data: {"type":"item_status","item_id":2,"job_id":2,"status":"downloading", ...}

event: ping
data: {"ts":1777251676}
```

Notas frontend:

- Abrir una sola conexion SSE por sesion.
- Reconectar automaticamente en error/cierre.
- Al reconectar, hacer refetch de `GET /api/jobs` para consistencia.

---

## 5) Estados de item (UI)

Estados observables:

- `queued`
- `downloading`
- `processing`
- `pending_device_online`
- `transferring`
- `completed`
- `failed`
- `canceled`

Acciones recomendadas:

1. `queued/downloading/processing/transferring`:
   - mostrar progreso
   - habilitar cancelar por job
2. `failed/canceled/pending_device_online`:
   - habilitar retry por item
3. `completed`:
   - habilitar download

---

## 6) Flujos recomendados en frontend

### Flujo A: Inicio de app

1. `GET /api/auth/me`
2. Si `200`, cargar dashboard.
3. Si `401`, redirigir a login.

### Flujo B: Crear descarga

1. `POST /api/jobs`
2. Actualizar lista local con respuesta.
3. SSE actualiza progreso de items.

### Flujo C: Recuperacion tras desconexion SSE

1. Reconectar SSE.
2. Ejecutar `GET /api/jobs`.
3. Reconciliar cache local con backend.

### Flujo D: Cancelar y reintentar

1. `POST /api/jobs/{id}/cancel`
2. Esperar estado `canceled` en item.
3. `POST /api/items/{item_id}/retry`
4. Verificar vuelta a `queued/downloading`.
