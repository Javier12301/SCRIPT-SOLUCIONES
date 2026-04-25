## V1.1 - Descargador Personal Multiusuario Seguro (FastAPI + React + yt_dlp nativo)

### Resumen
- Se mantiene la base de V1, pero ahora orientada a uso familiar: **multiusuario con aislamiento completo**, frontend **React + Vite**, cola de descargas, acceso remoto por **Tailscale/MagicDNS**, y motor de descarga con **`import yt_dlp`** (sin `.exe` ni parseo de consola).
- Factibilidad validada: `yt_dlp` soporta `progress_hooks` y `postprocessor_hooks`; FastAPI cubre CORS específico y SSE/streaming.
- Alcance V1.1: descarga local en PC por usuario + descarga posterior desde móvil/PC; Google Drive sigue fuera (v2).

### Cambios de arquitectura e interfaces
- Modelo de datos:
  - `users(id, username UNIQUE, password_hash, role)` con roles `admin|user`.
  - `jobs` agrega `user_id` FK.
  - `settings` agrega `user_id` FK (settings por usuario; opcionalmente una fila global admin para defaults).
  - `job_items` referencia `job_id` y hereda aislamiento por join con `jobs.user_id`.
- Aislamiento backend obligatorio:
  - Todo endpoint de jobs/items filtra por `current_user.id`.
  - Prohibido acceso cruzado: si el recurso no pertenece al usuario autenticado, responde `404` (no filtra existencia).
- Aislamiento de archivos:
  - Carpeta base: `downloads/{username}/...`.
  - Plantilla de salida por job/item sanitizada y sin traversal (`..`, rutas absolutas, caracteres inválidos).
- Motor de descarga (nativo):
  - Implementación con `yt_dlp.YoutubeDL(...)` embebido en Python.
  - Progreso en tiempo real con `progress_hooks` (+ `postprocessor_hooks` para ffmpeg).
  - Prohibido usar `subprocess` para ejecutar `yt-dlp.exe`.
- SQLite concurrencia:
  - Al iniciar app: `PRAGMA journal_mode=WAL;`, `PRAGMA synchronous=NORMAL;`, `PRAGMA busy_timeout=5000;`.
  - Escrituras de progreso vía transacciones cortas y batching ligero para minimizar lock contention.
- Endpoint admin de mantenimiento:
  - `POST /api/admin/update-extractor` (solo `admin`) ejecuta actualización de paquete (`python -m pip install --upgrade yt-dlp`) en tarea controlada.
  - Devuelve estado y versión previa/nueva.
  - Tras update, se intenta `importlib.reload(yt_dlp)`; si no aplica completamente, se marca `restart_recommended=true` sin tumbar servicio.
- API pública (actualizada):
  - Auth/sesión: `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`.
  - Jobs: `POST /api/jobs`, `GET /api/jobs`, `GET /api/jobs/{id}`, `POST /api/jobs/{id}/cancel`.
  - Items/archivos: `POST /api/items/{id}/retry`, `GET /api/items/{id}/download`.
  - Streaming estado: `GET /api/events` (SSE por usuario autenticado).
  - Admin: `POST /api/admin/update-extractor`.
- Frontend React:
  - Login + dashboard reactivo con tabla de jobs/items y reconexión SSE.
  - Estado centralizado para merges incrementales de eventos.
  - Vistas por rol: funciones admin visibles solo para `admin`.

### Red, seguridad y operación
- Red:
  - Uso operativo por Tailscale + MagicDNS (ej. `http://pc-server:8000`).
  - CORS restringido a origins explícitos: host de MagicDNS y localhost dev.
- Seguridad:
  - Password hash con Argon2/bcrypt.
  - Sesión segura con expiración; cookies `HttpOnly` (y `Secure` cuando aplique HTTPS local/túnel).
  - Rate limit en login y en endpoint admin.
- Cola/rendimiento:
  - Modo default secuencial (`concurrency=1`), configurable.
  - Errores por item no frenan lote.
  - Persistencia de estado para recuperación tras reinicio.

### Plan de pruebas (aceptación)
- Multiusuario:
  - Usuario A no puede listar/ver/descargar/cancelar jobs de B.
  - Archivos quedan físicamente en `downloads/A` y `downloads/B` sin mezcla.
- Descarga nativa:
  - `progress_hooks` actualiza porcentaje/estado en DB y se refleja en SSE.
  - Flujo audio/video con ffmpeg postprocesado finaliza con estado correcto.
- SQLite WAL:
  - Con UI consultando + worker escribiendo progreso no aparece `database is locked` en carga normal.
- Admin extractor:
  - `user` recibe `403`; `admin` actualiza versión correctamente.
  - Si reload no aplica, respuesta marca `restart_recommended` sin caída del servicio.
- Frontend:
  - Reconexión SSE tras corte breve de red.
  - Tabla reactiva mantiene consistencia de estados y progreso.

### Supuestos y defaults
- Stack fijado: **FastAPI + SQLite + React/Vite**.
- Roles fijados: **`admin` y `user`**.
- `yt_dlp` embebido como módulo Python para descargas; `subprocess` permitido solo para actualización administrativa de paquete.
- Google Drive y transferencia automática a otros dispositivos quedan explícitamente para v2.
