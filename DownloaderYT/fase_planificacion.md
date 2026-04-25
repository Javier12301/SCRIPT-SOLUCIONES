# Fase Planificacion - DownloaderYT V1.1

## Estado global

- Proyecto: `DownloaderYT`
- Metodologia: desarrollo iterativo por fases (0 a 6)
- Regla: no avanzar de fase sin aprobacion explicita del usuario

## Checklist de fases

- [x] Fase 0 - Arquitectura
- [x] Fase 1 - Infraestructura de datos
- [x] Fase 2 - Seguridad y usuarios
- [x] Fase 3 - Motor core (yt_dlp + worker + SMB)
- [ ] Fase 4 - API REST + SSE
- [ ] Fase 5 - Frontend base
- [ ] Fase 6 - Frontend dinamico

---

## Fase 0 - Arquitectura

**Estado:** completada  
**Fecha:** 2026-04-25

### Cambios implementados

1. Se creo `DownloaderYT/arquitectura.md` con el diseno final V1.1.
2. Se documentaron:
   - objetivo y alcance
   - arquitectura backend y frontend
   - modelo de datos y ownership por usuario
   - estados de `job_items`
   - flujo de auto-transferencia SMB con ping y reintentos
   - contrato API (auth, jobs, items, SSE, admin)
   - operacion (Tailscale/MagicDNS, CORS, `.env`, backups)
3. Se agregaron diagramas Mermaid:
   - flujo principal de procesamiento y transferencia
   - flujo de actualizacion de extractor (`/api/admin/update-extractor`)

### Resultado esperado de la fase

- Base de arquitectura lista para comenzar implementacion tecnica en Fase 1.

---

## Fase 1 - Infraestructura de datos

**Estado:** completada  
**Fecha:** 2026-04-25

### Cambios implementados

1. Se estructuro el proyecto en carpetas:
   - `backend/`
   - `frontend/`
   - `docs/`
2. Se movio la documentacion actual a `docs/`:
   - `docs/arquitectura.md`
   - `docs/documentacion.md`
3. Se creo la base de backend FastAPI:
   - `backend/app/main.py`
   - routers base (`auth`, `jobs`, `items`, `events`, `admin`)
   - dependencias API base (`backend/app/api/dependencies.py`)
4. Se implemento configuracion inicial con `pydantic-settings`:
   - `backend/app/core/config.py`
   - `.env.example` en backend
5. Se implemento capa de datos SQLAlchemy + SQLite:
   - `backend/app/db/database.py`
   - `backend/app/db/models.py`
6. Se configuraron PRAGMAs de SQLite en conexion:
   - `journal_mode=WAL`
   - `synchronous=NORMAL`
   - `busy_timeout=5000`
   - `foreign_keys=ON`
7. Se dejo Alembic listo:
   - `backend/alembic.ini`
   - `backend/alembic/env.py`
   - `backend/alembic/script.py.mako`
   - migracion inicial `backend/alembic/versions/0001_initial_schema.py`
8. Se agrego base minima de frontend para estructura de trabajo:
   - `frontend/package.json`
   - `frontend/vite.config.js`
   - `frontend/index.html`
   - `frontend/src/main.jsx`
   - `frontend/src/app/App.jsx`

### Resultado esperado de la fase

- Infraestructura inicial y base de datos versionada listas para avanzar a Fase 2.

---

## Fase 2 - Seguridad y usuarios

**Estado:** completada  
**Fecha:** 2026-04-25

### Cambios implementados

1. Se implemento seguridad base:
   - `backend/app/core/security.py`
   - hashing de password (`passlib[argon2]`)
   - emision y hash de token de sesion
2. Se implemento almacenamiento de sesiones en DB:
   - `backend/app/db/session_store.py`
   - creacion, validacion, revocacion y `last_seen_at`
3. Se implementaron endpoints de autenticacion funcionales:
   - `POST /api/auth/login`
   - `POST /api/auth/logout`
   - `GET /api/auth/me`
4. Se implementaron dependencias de seguridad:
   - `get_current_user` por cookie de sesion
   - `require_admin` por rol
5. Se protegio endpoint admin con rol:
   - `POST /api/admin/update-extractor` requiere sesion admin valida
6. Se agrego bootstrap de admin inicial en `init_db` para entorno local:
   - configurable por `.env` (`APP_BOOTSTRAP_ADMIN_*`)
7. Se agregaron tests HTTP de contrato para auth + admin y pruebas de infraestructura.

### Resultado esperado de la fase

- Backend con autenticacion por sesion operativa y base lista para avanzar al motor de descargas (Fase 3).

---

## Fase 3 - Motor core (yt_dlp + worker + SMB)

**Estado:** completada  
**Fecha:** 2026-04-25

### Cambios implementados

1. Se implemento wrapper nativo de `yt_dlp`:
   - `backend/app/services/downloader.py`
   - soporte de hooks de progreso y postprocesado
2. Se implemento bus de eventos interno:
   - `backend/app/services/event_bus.py`
3. Se implemento worker secuencial en background:
   - `backend/app/services/queue_worker.py`
   - ciclo `queued -> downloading -> processing -> (transfer) -> completed`
4. Se implemento flujo SMB/Tailscale:
   - deteccion host UNC
   - ping previo (`pending_device_online` + `next_retry_at`)
   - transferencia (`transferring`) con `shutil.copy2`
   - eliminacion de archivo local al completar transferencia
5. Se conecto startup/shutdown de worker en la app:
   - `backend/app/main.py`
   - `backend/app/services/__init__.py`
6. Se agregaron pruebas unitarias y de integracion de servicios fase 3.

### Resultado esperado de la fase

- Motor de descarga y cola de procesamiento listos para exponer por API en Fase 4.

---

## Fase 4 - API REST + SSE

**Estado:** pendiente

### Objetivo

- Implementar endpoints funcionales con aislamiento estricto por usuario y eventos en tiempo real.

---

## Fase 5 - Frontend base

**Estado:** pendiente

### Objetivo

- Inicializar React/Vite + estado base (Zustand/TanStack Query) + login/layout.

---

## Fase 6 - Frontend dinamico

**Estado:** pendiente

### Objetivo

- Dashboard reactivo con SSE, acciones de operacion y control de items/jobs.
