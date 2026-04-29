# Helpers de desarrollo y testing (Windows + PowerShell)

Todos los comandos se ejecutan desde la raiz del proyecto:

`D:\JAVIER\SCRIPT-PERSONALES\DownloaderYT`

## 1) Levantar backend (FastAPI con reload)

```powershell
.\scripts\backend-dev.ps1
```

Opcional (host/puerto):

```powershell
.\scripts\backend-dev.ps1 -Host 0.0.0.0 -Port 8000
```

URL esperada:

- `http://127.0.0.1:8000/api/health`
- `http://127.0.0.1:8000/docs`

## 2) Levantar frontend (Vite)

```powershell
.\scripts\frontend-dev.ps1
```

URL esperada (por defecto):

- `http://127.0.0.1:5173`

## 3) Ejecutar tests backend (fase 1)

```powershell
.\scripts\backend-test.ps1
```

Filtrar por nombre:

```powershell
.\scripts\backend-test.ps1 -Keyword "health or pragmas"
```

## 4) Probar endpoints (manual, estilo backend tradicional)

Swagger UI:

- `http://127.0.0.1:8000/docs`

Con `curl` (PowerShell) y cookie jar:

```powershell
# 1) login (guarda cookie en cookie.txt)
curl.exe -i -c cookie.txt -X POST "http://127.0.0.1:8000/api/auth/login" `
  -H "Content-Type: application/json" `
  -d "{\"username\":\"admin\",\"password\":\"admin1234\"}"

# 2) me (usa cookie guardada)
curl.exe -i -b cookie.txt "http://127.0.0.1:8000/api/auth/me"

# 3) endpoint admin (autenticado)
curl.exe -i -b cookie.txt -X POST "http://127.0.0.1:8000/api/admin/update-extractor"

# 4) logout
curl.exe -i -b cookie.txt -c cookie.txt -X POST "http://127.0.0.1:8000/api/auth/logout"
```

## 5) Ejecucion directa (sin helpers)

Backend:

```powershell
Set-Location .\backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Tests:

```powershell
Set-Location .\backend
..\.venv\Scripts\python.exe -m pytest -q tests
```

## Checklist por fase (Swagger)

### Fase 2 (auth y usuarios) - que debes probar

1. `POST /api/auth/login` con `admin/admin1234`.
2. `GET /api/auth/me` luego del login.
3. `POST /api/auth/logout`.
4. `GET /api/auth/me` despues de logout (debe fallar con 401).
5. `POST /api/admin/update-extractor`:
   - sin login: 401
   - con admin logueado: 200

### Fase 2 - que debe funcionar

1. Se crea cookie de sesion al loguear.
2. `me` devuelve usuario autenticado.
3. `logout` invalida sesion.
4. Endpoint admin exige rol admin.

### Fase 3 (motor core) - que debes probar en Swagger ahora

1. Repetir smoke de Fase 2 para validar que no hubo regresiones.
2. `GET /api/health` debe responder `{"status":"ok"}`.

### Fase 3 - que debe funcionar internamente

1. Worker secuencial de cola levantado en startup.
2. Flujo de estados base:
   - `queued -> downloading -> processing -> completed`
3. Con transferencia activa:
   - host no disponible: `pending_device_online`
   - host disponible: `transferring -> completed` y elimina archivo local
4. Publicacion de eventos internos por usuario para futura SSE (Fase 4).

### Fase 4 (API REST + SSE) - que debes probar en Swagger

1. Login admin:
   - `POST /api/auth/login` con `admin/admin1234`
2. Crear job de video simple:
   - `POST /api/jobs` con una URL de video.
3. Crear job de playlist:
   - `POST /api/jobs` con URL de playlist.
4. Listar jobs:
   - `GET /api/jobs`
5. Ver detalle de job:
   - `GET /api/jobs/{id}`
6. Cancelar job:
   - `POST /api/jobs/{id}/cancel`
7. Reintentar item en estado fallido/canceled:
   - `POST /api/items/{id}/retry`
8. SSE:
   - `GET /api/events`
9. Download de item:
   - `GET /api/items/{id}/download` (solo cuando status sea `completed` y archivo exista)

### Fase 4 - que debe funcionar

1. `POST /api/jobs`:
   - video normal -> crea 1 `job_item`
   - playlist -> crea N `job_items` (uno por video)
2. `config_json` conserva estructura flexible:
   - acepta `cookies_path`, `ytdlp_options` y campos extra (compatibilidad V2)
3. Ownership estricto:
   - recursos de otro usuario devuelven `404`
4. Cancel/retry:
   - cancel marca job/items activos en `canceled`
   - retry solo permite estados validos (`failed`, `canceled`, `pending_device_online`)
   - cancel durante descarga activa debe cortar el item en curso (no debe terminar en `completed`)
5. SSE por usuario:
   - no mezcla eventos de otros usuarios
6. Download:
   - solo para item `completed` y archivo disponible
