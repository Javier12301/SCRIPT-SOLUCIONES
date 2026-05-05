# Plan Frontend - DownloaderYT V1.1

## 0. Estado De Implementacion

Estado actualizado tras la primera implementacion de interfaz.

### Resuelto

- Dependencias planificadas instaladas: `react-hook-form`, `zod`, `@hookform/resolvers`, `lucide-react` y `clsx`.
- `App.jsx` reemplazado por providers y `RouterProvider`.
- `app/providers.jsx` creado con `QueryClientProvider`.
- `app/router.jsx` creado con rutas publicas, protegidas y proteccion por rol admin.
- Cliente HTTP `services/api.js` creado con `axios`, `VITE_API_URL` y `withCredentials`.
- `services/queryClient.js` creado con defaults de TanStack Query.
- `services/sse.js` creado para abrir `/api/events`.
- `store/uiStore.js` creado para estado local de UI y estado SSE.
- `store/authStore.js` creado como cache local ligera si hace falta.
- Utilidades creadas para formatear fechas, bytes, velocidad, ETA, estados y URLs.
- Componentes UI base creados: `Button`, `Card`, `Badge`, `ProgressBar`, `Avatar`.
- Componentes layout creados: `Brand`, `Sidebar`, `Topbar`, `BottomNav`, `AppShell`.
- Login responsive implementado con React Hook Form + Zod y `POST /api/auth/login`.
- `GET /api/auth/me` implementado para bootstrap de sesion y redirecciones.
- Logout implementado contra `POST /api/auth/logout`.
- Home de usuario implementado con formulario de descarga, modo una URL/varias URLs, opciones avanzadas, activas y recientes.
- Jobs conectados a `GET /api/jobs`, `POST /api/jobs`, `POST /api/jobs/{job_id}/cancel`, `POST /api/items/{item_id}/retry` y descarga por `GET /api/items/{item_id}/download`.
- SSE conectado con merge basico de eventos `item_status` sobre cache de `['jobs']` y refetch en error/reconexion.
- Panel admin responsive implementado con metricas, usuarios mock, politicas mock, actividad mock y modal real de crear usuario con `POST /api/auth/register`.
- CSS global responsive implementado con tokens visuales, sidebar desktop, bottom nav mobile, cards, formularios, tablas/listas adaptativas y login mobile/desktop.
- Build verificado con `npm run build` y completado correctamente.

### Pendiente O Limitado Por Backend

- Listado real de usuarios admin sigue usando mock hasta que exista `GET /api/admin/users`.
- Edicion/suspension/activacion de usuarios sigue visual hasta que existan endpoints admin.
- Politicas del sistema siguen visuales hasta `GET/PUT /api/admin/policies`.
- Actividad reciente admin sigue mock hasta endpoint de auditoria.
- Metricas admin siguen mock hasta `GET /api/admin/metrics`.
- Cupo diario restante sigue calculado de forma visual/local hasta `GET /api/me/usage`.
- Google Drive y WhatsApp permanecen como futuras integraciones backend.

## 1. Objetivo

Implementar el frontend de DownloaderYT dentro de `frontend/` usando React + Vite, con una experiencia visual cercana a los disenos provistos para desktop y mobile.

El frontend debe cubrir:

- Login responsive.
- Inicio de usuario para crear descargas desde una o varias URLs.
- Seguimiento de descargas activas y recientes.
- Acciones sobre items/jobs: cancelar, reintentar y descargar.
- Panel admin visual para gestion de usuarios, metricas, politicas y actividad.
- Integracion real con los endpoints existentes.
- Preparacion clara para endpoints backend faltantes.

## 2. Alcance Real Actual

Segun `docs/frontend_endpoints.md`, actualmente existen endpoints para:

- `POST /api/auth/login`
- `POST /api/auth/logout`
- `POST /api/auth/register`
- `GET /api/auth/me`
- `POST /api/jobs`
- `GET /api/jobs`
- `GET /api/jobs/{job_id}`
- `POST /api/jobs/{job_id}/cancel`
- `POST /api/items/{item_id}/retry`
- `GET /api/items/{item_id}/download`
- `GET /api/events`
- `POST /api/admin/update-extractor`

La UI se construira completa, pero las secciones sin backend real se dejaran documentadas y aisladas para poder conectarlas luego sin reescribir componentes.

## 3. Decisiones Tecnicas

- No usar una libreria UI pesada. El diseno es personalizado y conviene mantener componentes propios.
- Usar CSS propio con tokens globales para replicar el estilo naranja, limpio y familiar de los mockups.
- Usar `TanStack Query` para todo server-state.
- Usar `Zustand` solo para estado local de UI.
- Usar `React Hook Form` para formularios performantes.
- Usar `Zod` para validar payloads antes de llamar al backend.
- Usar `lucide-react` para iconografia consistente y tree-shakeable.
- Usar `React Router` con layouts anidados y rutas protegidas por sesion/rol.
- Mantener una sola conexion SSE por sesion autenticada.

## 4. Librerias

### 4.1 Ya Instaladas

- `react`: UI basada en componentes.
- `react-dom`: renderizado web.
- `react-router-dom`: rutas SPA, layouts y proteccion de vistas.
- `@tanstack/react-query`: cache, server-state, mutations e invalidaciones.
- `zustand`: estado local liviano.
- `axios`: cliente HTTP.
- `vite`: bundler/dev server.

### 4.2 Nuevas Librerias Planificadas

- `react-hook-form`: formularios con menos re-renders, especialmente login, crear usuario, descarga y politicas.
- `zod`: schemas de validacion para formularios y payloads.
- `@hookform/resolvers`: puente entre React Hook Form y Zod.
- `lucide-react`: iconos SVG por import individual, con buen tree-shaking.
- `clsx`: composicion segura de clases condicionales.

### 4.3 Opcionales Posteriores

- `date-fns`: si los formatters manuales de fechas crecen.
- `@tanstack/react-virtual`: si las listas de descargas o usuarios crecen mucho y requieren virtualizacion.

## 5. Referencias Investigadas Con Context7

### React 19

Aplicaciones:

- Usar componentes pequenos y composables.
- Evitar efectos innecesarios para estado derivado.
- Usar `useEffectEvent` en integraciones como SSE cuando haga falta acceder a valores actuales sin reabrir conexiones por dependencias irrelevantes.
- Usar `useDeferredValue` en busquedas de listas si se detectan renders costosos.
- Usar `startTransition` para navegaciones o filtros no urgentes si la UI se siente bloqueada.

### TanStack Query v5

Aplicaciones:

- `QueryClientProvider` en `app/providers.jsx`.
- Query keys estables: `['auth', 'me']`, `['jobs']`, `['jobs', jobId]`, `['admin', 'users']`.
- Invalidar `['jobs']` despues de crear, cancelar o reintentar.
- Usar `queryClient.setQueryData` para mezclar eventos SSE en cache.
- Refetch al reconectar SSE para consistencia.
- Usar optimistic updates solo en acciones simples y reversibles; preferir invalidacion si hay duda.

### React Router 7

Aplicaciones:

- Usar rutas anidadas con layouts.
- Separar `PublicLayout`, `UserLayout` y `AdminLayout` si hace falta.
- Proteger rutas con `RequireAuth` y `RequireRole`.
- Redirigir usuarios autenticados fuera de `/login`.
- Redirigir usuarios sin rol admin fuera de `/admin/*`.

### Zustand 5

Aplicaciones:

- Guardar solo estado local de UI: sidebar, tema, menu mobile, estado de conexion SSE.
- No guardar jobs ni usuarios reales en Zustand porque son server-state.
- Usar selectores para evitar re-renders.
- Usar `persist` solo para preferencias no sensibles como tema o idioma visual.

### React Hook Form

Aplicaciones:

- Formularios no controlados por defecto.
- `handleSubmit` para login, creacion de usuario y descarga.
- `formState.isSubmitting` para bloquear doble envio.
- `reset` tras operaciones exitosas.
- `useFormState` si formularios grandes empiezan a renderizar demasiado.

### Zod

Aplicaciones:

- Validar username/password en login.
- Validar URL unica y listas multi-URL.
- Validar crear usuario.
- Validar politicas admin cuando backend exista.
- Usar `safeParse` cuando se validen datos no confiables fuera de formularios.

### Lucide React

Aplicaciones:

- Importar iconos individualmente para tree-shaking.
- Usar `size`, `strokeWidth` y `currentColor` desde CSS.
- Agregar `aria-hidden="true"` en iconos decorativos.
- Icon buttons deben tener `aria-label`.

## 6. Arquitectura De Carpetas

```txt
frontend/src/
├── app/
│   ├── App.jsx
│   ├── router.jsx
│   └── providers.jsx
├── components/
│   ├── layout/
│   │   ├── AppShell.jsx
│   │   ├── Sidebar.jsx
│   │   ├── Topbar.jsx
│   │   ├── BottomNav.jsx
│   │   ├── Brand.jsx
│   │   ├── PageHeader.jsx
│   │   └── MobileHeader.jsx
│   ├── jobs/
│   │   ├── DownloadForm.jsx
│   │   ├── UrlModeTabs.jsx
│   │   ├── AdvancedOptions.jsx
│   │   ├── MultiUrlBox.jsx
│   │   ├── ActiveDownloads.jsx
│   │   ├── RecentDownloads.jsx
│   │   ├── JobItemRow.jsx
│   │   └── StatusBadge.jsx
│   └── ui/
│       ├── Avatar.jsx
│       ├── Badge.jsx
│       ├── Button.jsx
│       ├── Card.jsx
│       ├── DropdownMenu.jsx
│       ├── EmptyState.jsx
│       ├── IconButton.jsx
│       ├── Input.jsx
│       ├── LoadingState.jsx
│       ├── MetricCard.jsx
│       ├── ProgressBar.jsx
│       ├── Select.jsx
│       ├── Tabs.jsx
│       └── Textarea.jsx
├── features/
│   ├── auth/
│   │   ├── LoginPage.jsx
│   │   ├── LoginForm.jsx
│   │   ├── auth.api.js
│   │   ├── auth.schemas.js
│   │   └── useAuth.js
│   ├── jobs/
│   │   ├── HomePage.jsx
│   │   ├── jobs.api.js
│   │   ├── jobs.queries.js
│   │   ├── jobs.schemas.js
│   │   └── useJobsEvents.js
│   └── admin/
│       ├── AdminPage.jsx
│       ├── AdminMetricGrid.jsx
│       ├── AdminUsersPanel.jsx
│       ├── AdminPoliciesPanel.jsx
│       ├── AdminActivityPanel.jsx
│       ├── CreateUserModal.jsx
│       ├── admin.api.js
│       ├── admin.mock.js
│       └── admin.schemas.js
├── services/
│   ├── api.js
│   ├── queryClient.js
│   └── sse.js
├── store/
│   ├── authStore.js
│   └── uiStore.js
├── styles/
│   ├── globals.css
│   ├── tokens.css
│   └── responsive.css
└── utils/
    ├── formatters.js
    ├── jobs.js
    └── status.js
```

## 7. Rutas

```txt
/login
/app/inicio
/app/descargas
/app/recientes
/app/ajustes
/admin/resumen
/admin/usuarios
/admin/limites
/admin/ajustes
```

Reglas:

- No autenticado: redirigir a `/login`.
- Autenticado normal: permitir `/app/*`.
- Admin: permitir `/app/*` y `/admin/*`.
- Usuario normal en `/admin/*`: redirigir a `/app/inicio`.
- Usuario autenticado en `/login`: redirigir segun rol.

## 8. Diseno Visual

### 8.1 Paleta

```txt
--color-primary: #ff5a00;
--color-primary-hover: #ea4f00;
--color-primary-soft: #fff3e8;
--color-primary-soft-strong: #ffe3ca;
--color-background: #fffaf5;
--color-surface: #ffffff;
--color-surface-muted: #fff7ef;
--color-border: #f1dfd0;
--color-border-strong: #ffc28f;
--color-text: #20242a;
--color-text-muted: #6b7280;
--color-success: #22c55e;
--color-success-soft: #dcfce7;
--color-warning: #f59e0b;
--color-warning-soft: #fff7db;
--color-danger: #ef4444;
--color-danger-soft: #fee2e2;
--color-info: #3b82f6;
--color-info-soft: #dbeafe;
--color-purple: #8b5cf6;
--color-purple-soft: #ede9fe;
```

### 8.2 Tipografia

- Fuente principal: system UI (`Inter` no se agrega salvo que se decida cargar fuente externa).
- Titulos desktop: 22px a 28px.
- Titulos mobile: 20px a 24px.
- Texto base: 14px a 16px.
- Texto auxiliar: 12px a 13px.
- Peso principal: 500/600 para controles y titulos.

### 8.3 Espaciado Y Radios

```txt
--radius-sm: 8px;
--radius-md: 12px;
--radius-lg: 16px;
--radius-xl: 22px;
--shadow-card: 0 10px 30px rgba(24, 24, 27, 0.06);
--shadow-popover: 0 16px 40px rgba(24, 24, 27, 0.14);
```

## 9. Responsive

Breakpoints:

```txt
mobile: <= 767px
tablet: 768px - 1023px
desktop: >= 1024px
wide: >= 1280px
```

Desktop:

- Sidebar fijo de 260px aproximados.
- Topbar superior.
- Contenido con cards.
- Home con columna principal y resumen lateral.
- Admin con metricas horizontales y tablas.

Mobile:

- Sin sidebar.
- Header compacto.
- Bottom nav fijo.
- Cards apiladas.
- Tablas convertidas a filas tipo tarjeta.
- Botones principales full-width.
- Inputs tactiles con altura minima de 44px.

## 10. Componentes Principales

### 10.1 Login

- `LoginPage`: layout desktop/mobile.
- `LoginForm`: form conectado a `POST /api/auth/login`.
- `LanguageSelector`: visual inicialmente.
- `WaveBackground`: ondas inferiores estilo mockup.
- `Brand`: logo y nombre.

### 10.2 Inicio Usuario

- `DownloadForm`: URL unica o multiples URLs.
- `UrlModeTabs`: `Una URL` y `Varias URLs`.
- `AdvancedOptions`: cookies y opciones extra.
- `ActiveDownloads`: descargas en progreso.
- `RecentDownloads`: items completados o recientes.
- `QuickSummary`: resumen diario, idioma, ayuda, seguridad.

### 10.3 Admin

- `AdminMetricGrid`: tarjetas de metricas.
- `AdminUsersPanel`: lista/tabla de usuarios.
- `CreateUserModal`: usa endpoint real `POST /api/auth/register`.
- `AdminPoliciesPanel`: visual hasta que existan endpoints de politicas.
- `AdminActivityPanel`: visual hasta que exista endpoint de auditoria.

## 11. Estado De Datos

### 11.1 TanStack Query

Query keys:

```js
['auth', 'me']
['jobs']
['jobs', jobId]
['admin', 'users']
['admin', 'metrics']
['admin', 'activity']
['admin', 'policies']
```

Uso:

- `useQuery` para `me`, jobs y futuros datos admin.
- `useMutation` para login, logout, crear job, cancelar, reintentar, crear usuario.
- `invalidateQueries({ queryKey: ['jobs'] })` despues de mutaciones que cambian descargas.
- `setQueryData(['jobs'], updater)` para eventos SSE.

### 11.2 Zustand

Stores:

- `authStore`: cache local ligera del usuario si hace falta, sin reemplazar `GET /api/auth/me`.
- `uiStore`: tema, sidebar, menu mobile, estado SSE, idioma visual.

No guardar en Zustand:

- Jobs.
- Items.
- Usuarios admin reales.
- Metricas backend.

## 12. SSE

Archivo: `services/sse.js` y hook `features/jobs/useJobsEvents.js`.

Reglas:

- Abrir una sola conexion a `/api/events` cuando haya sesion.
- Usar cookies del navegador.
- En `connected`: marcar UI como conectado.
- En `message`: mezclar evento en cache de `['jobs']`.
- En error/cierre: marcar reconectando.
- Al reconectar: invalidar/refetch `['jobs']`.

## 13. Formularios Y Validacion

### 13.1 Login

Schema:

- `username`: requerido, minimo 1.
- `password`: requerido, minimo 1.

### 13.2 Crear Descarga

Schema:

- `mode`: `single` o `multi`.
- `url`: URL requerida si `single`.
- `urlsText`: una o mas URLs validas si `multi`.
- `format`: `video_mp4` o `audio_mp3`.
- `cookiesPath`: opcional.
- `extraOptions`: opcional.

Payload:

```js
{
  sources,
  config: {
    output_profile,
    cookies_path,
    ytdlp_options
  }
}
```

### 13.3 Crear Usuario

Schema:

- `username`: requerido.
- `password`: requerido.
- `confirmPassword`: debe coincidir.

Payload actual:

```js
{
  username,
  password
}
```

## 14. Estados De Descarga

```txt
queued -> En cola
downloading -> Descargando
processing -> Preparando archivo
pending_device_online -> Esperando dispositivo
transferring -> Transfiriendo
completed -> Completado
failed -> Error
canceled -> Cancelado
```

Acciones:

- `queued`, `downloading`, `processing`, `transferring`: cancelar job.
- `failed`, `canceled`, `pending_device_online`: reintentar item.
- `completed`: descargar archivo.

## 15. Performance

- Evitar renders globales con Zustand selectors.
- No guardar server-state duplicado.
- Usar `React.memo` solo si hay evidencia de renders costosos.
- Usar `useDeferredValue` en busquedas de usuarios/descargas si la lista crece.
- Usar lazy loading por ruta para admin si el bundle crece.
- Importar iconos Lucide individualmente.
- Mantener CSS simple y sin runtime CSS-in-JS.
- Considerar virtualizacion solo si las listas superan cientos de filas visibles.

## 16. Accesibilidad

- Botones icon-only con `aria-label`.
- Iconos decorativos con `aria-hidden="true"`.
- Contraste suficiente entre naranja y texto.
- Foco visible en inputs, botones y menus.
- Inputs con `label` real o `aria-label`.
- Estados de error visibles y legibles.
- Navegacion mobile tactil con targets minimos de 44px.

## 17. Fases De Implementacion

### Fase A - Base Visual

- CSS global, tokens y reset.
- Componentes UI base.
- Brand, layout desktop/mobile.

### Fase B - App Shell Y Routing

- Providers.
- Router.
- Rutas protegidas.
- Shell usuario/admin.

### Fase C - Auth

- Login real.
- Logout.
- `GET /api/auth/me` al iniciar.
- Redirecciones por rol.

### Fase D - Home Usuario

- Formulario descarga.
- Listas activas y recientes.
- Acciones basicas.

### Fase E - API Jobs + SSE

- Crear jobs.
- Listar jobs.
- Cancelar/reintentar/descargar.
- Conexion SSE y merge en cache.

### Fase F - Admin Visual

- Panel admin responsive.
- Crear usuario real.
- Mock aislado para usuarios, metricas, politicas y actividad faltantes.

### Fase G - Pulido Y Build

- Ajuste responsive contra mockups.
- Estados vacios/carga/error.
- `npm run build`.

## 18. Criterios De Aceptacion

- Login funciona con cookie HTTP-only.
- Usuario autenticado entra a dashboard.
- Admin puede entrar a panel admin.
- Usuario no admin no puede ver `/admin/*`.
- Crear descarga llama `POST /api/jobs` con payload correcto.
- Descargas se listan desde `GET /api/jobs`.
- SSE actualiza progreso o fuerza refetch al reconectar.
- Cancelar/reintentar/descargar usan endpoints reales.
- Mobile replica estructura de mockups con bottom nav.
- Desktop replica sidebar/topbar/cards de mockups.
- Build de Vite pasa sin errores.
