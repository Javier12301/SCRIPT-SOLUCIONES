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
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir .\backend --reload
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
