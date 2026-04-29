# Memoria de Contexto - DownloaderYT

## Estado del proyecto (al cierre de sesion)

- Proyecto activo: `DownloaderYT` (trabajar solo aqui).
- Fases completadas:
  - Fase 0: Arquitectura
  - Fase 1: Infraestructura de datos
  - Fase 2: Auth y usuarios
  - Fase 3: Motor core (`yt_dlp` + worker + SMB)
  - Fase 4: API REST + SSE
- Fases pendientes:
  - Fase 5: Frontend base
  - Fase 6: Frontend dinamico

## Validacion funcional reportada por usuario

### Auth (Fase 2)

1. `POST /api/auth/login` con `admin/admin1234` funciona.
2. La tabla `sessions` muestra revocacion correcta de sesiones anteriores y nueva sesion activa.
3. `GET /api/auth/me` devuelve usuario autenticado (`admin`).
4. `POST /api/auth/logout` responde `logout ok (admin)`.
5. `GET /api/auth/me` despues de logout falla con `401 Not authenticated`.
6. `POST /api/admin/update-extractor`:
   - sin login -> `401 Not authenticated`
   - con login admin -> `200` placeholder de fase 4.

### Base backend (Fase 3 + base app)

1. `GET /api/health` responde `{"status":"ok"}`.
2. Worker de cola en background activo en startup.
3. Flujo interno de worker implementado:
   - `queued -> downloading -> processing -> completed`
   - con transferencia activa:
     - host offline -> `pending_device_online`
     - host online -> `transferring -> completed` y elimina archivo local

### API REST + SSE (Fase 4)

1. Endpoints funcionales implementados para `jobs`, `items`, `events`.
2. Expansion de playlists en `POST /api/jobs`:
   - una playlist crea multiples `job_items`.
3. `config_json` extensible para V2:
   - `cookies_path`, `ytdlp_options`, campos extra.
4. Ownership estricto:
   - recursos de otro usuario retornan `404`.
5. SSE operativo en `/api/events` por usuario autenticado.
6. Cancelacion robusta:
   - nuevo campo `job_items.cancel_requested`
   - cancel cooperativo en worker con throttling de consulta DB
   - evita carrera donde item cancelado terminaba en `completed`

## Preferencias de trabajo del usuario

1. Flujo de prueba preferido: Swagger UI (`/docs`), no `curl`.
2. Al cerrar cada fase se debe entregar checklist claro de:
   - que probar
   - que debe funcionar
3. Mantener comandos simples de arranque, estilo `npm run dev` / `dotnet run`.

## Comandos operativos definidos

Desde `D:\JAVIER\SCRIPT-PERSONALES\DownloaderYT`:

```powershell
.\scripts\backend-dev.ps1
.\scripts\frontend-dev.ps1
.\scripts\backend-test.ps1
```

Documentacion de apoyo:
- `docs/helpers_testing.md`
- `docs/arquitectura.md`
- `docs/documentacion.md`
- `fase_planificacion.md`

## Estado tecnico implementado

- Auth por cookie de sesion en DB (`login/logout/me`).
- Revocacion de sesion en logout.
- Proteccion de endpoint admin por rol.
- Bootstrap admin configurable por `.env`.
- Servicios core implementados:
  - `app/services/downloader.py`
  - `app/services/queue_worker.py`
  - `app/services/event_bus.py`
- Integracion startup/shutdown del worker en `app/main.py`.

## Cobertura de pruebas actual

- Suite backend en verde al cierre:
  - `23 passed`
- Tests clave:
  - contrato auth/admin
  - infraestructura DB y pragmas
  - servicios de worker/download/transfer

## Guia para futuros agentes

1. Leer primero:
   - `fase_planificacion.md`
   - `docs/helpers_testing.md`
   - esta memoria (`docs/memoria_contexto.md`)
2. Respetar el orden de fases y no mezclar trabajo de otros proyectos.
3. Si avanzan fase:
   - implementar
   - testear
   - dejar checklist Swagger (que probar / que debe funcionar)
4. Si necesitan referencia externa de librerias/frameworks:
   - usar MCP Context7 (`resolve_library_id` + `query_docs`) para documentacion actualizada.
   - preferir fuentes primarias/oficiales.

## Proximo objetivo recomendado

- Fase 5: frontend base (estado, layout, consumo de endpoints reales y flujo de autenticacion).
