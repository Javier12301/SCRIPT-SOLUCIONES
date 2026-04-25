# Documentación Técnica y UML - DownloaderYT V1.1

Este documento sirve como referencia central para entender la arquitectura, el flujo de datos y los conceptos operativos del sistema. Está diseñado para ser interpretado tanto por desarrolladores humanos como por agentes de IA.

## 0. Glosario de Conceptos Clave

Para entender este sistema, es fundamental distinguir los siguientes términos:

| Término | Definición | Contexto en el Proyecto |
| :--- | :--- | :--- |
| **Job (Tarea)** | Un contenedor lógico que agrupa una o varias solicitudes de descarga. | Cuando pegas una lista de URLs, se crea un *Job* que las contiene todas. |
| **JobItem (Ítem)** | La unidad mínima de trabajo. Corresponde a un único archivo/video a descargar. | Cada video de una playlist es un *JobItem*. Tiene su propio progreso y estado. |
| **SSE (Server-Sent Events)** | Tecnología que permite al servidor enviar actualizaciones en tiempo real al navegador. | Se usa para que veas el % de descarga y la velocidad sin que el navegador tenga que preguntar constantemente. |
| **SMB / UNC** | Protocolo de red para compartir archivos en Windows/Linux. | Permite que el servidor mueva automáticamente el archivo descargado a tu PC personal o NAS usando rutas como `\\MiPC\Descargas`. |
| **yt-dlp** | Herramienta de línea de comandos potente para descargar videos. | Es el "motor" interno. El proyecto lo usa de forma nativa para obtener la mejor calidad y compatibilidad. |
| **SQLite WAL** | *Write-Ahead Logging*. Un modo de alta eficiencia para la base de datos. | Permite que el servidor escriba información y el usuario lea el progreso simultáneamente sin bloqueos ni lentitud. |
| **Worker (Trabajador)** | Proceso de fondo independiente de la interfaz web. | Es el encargado de hacer el "trabajo sucio": descargar, convertir con FFmpeg y mover archivos por la red. |

---

## 1. Diagrama de Casos de Uso
Define las interacciones de los actores con el sistema.

```mermaid
graph LR
    subgraph Actores
        U((Usuario))
        A((Admin))
    end

    subgraph "DownloaderYT (Sistema)"
        UC1(Autenticarse)
        UC2(Crear Job de Descarga)
        UC3(Ver Progreso SSE)
        UC4(Cancelar Job/Item)
        UC5(Descargar Archivo Local)
        UC6(Configurar SMB)
        UC7(Actualizar Extractor)
        UC8(Gestionar Usuarios)
    end

    U --- UC1
    U --- UC2
    U --- UC3
    U --- UC4
    U --- UC5
    U --- UC6

    A --- UC7
    A --- UC8
    A -.-> U
```

## 2. Diagrama de Clases (Modelo de Datos)
Representa las entidades y sus relaciones en la base de datos SQLite.

```mermaid
classDiagram
    class User {
        +int id
        +string username
        +string password_hash
        +string role
        +datetime created_at
    }

    class Session {
        +int id
        +int user_id
        +string token_hash
        +datetime expires_at
        +datetime revoked_at
        +datetime last_seen_at
    }

    class Job {
        +int id
        +int user_id
        +string status
        +json config_json
        +datetime created_at
        +datetime updated_at
    }

    class JobItem {
        +int id
        +int job_id
        +string source_url
        +string status
        +float progress_pct
        +int downloaded_bytes
        +int total_bytes
        +string speed
        +string eta
        +string output_path
        +string error_message
        +datetime next_retry_at
    }

    class Setting {
        +int id
        +int user_id
        +string download_root_override
        +int concurrency
        +bool auto_transfer_enabled
        +string transfer_target_path
    }

    User "1" -- "*" Session : posee
    User "1" -- "*" Job : crea
    User "1" -- "1" Setting : configura
    Job "1" -- "*" JobItem : contiene
```

## 3. Diagrama de Estados (Ciclo de Vida de JobItem)
Muestra las transiciones de estado para un item individual.

```mermaid
stateDiagram-v2
    [*] --> pending: Creación
    pending --> queued: Agregado a cola
    queued --> downloading: Inicio descarga
    downloading --> processing: Post-procesamiento (FFmpeg)
    
    processing --> ready_for_transfer: Éxito (si SMB activo)
    processing --> completed: Éxito (si SMB inactivo)
    
    ready_for_transfer --> transferring: Ping exitoso
    ready_for_transfer --> pending_device_online: Ping fallido
    
    pending_device_online --> transferring: Reintento exitoso
    
    transferring --> completed: Transferencia OK
    
    downloading --> failed: Error red/extractor
    processing --> failed: Error FFmpeg
    transferring --> failed: Error copia SMB
    
    pending --> canceled: Cancelación manual
    queued --> canceled
    downloading --> canceled
    
    failed --> queued: Reintento manual
    completed --> [*]
    canceled --> [*]
```

## 4. Diagrama de Componentes (Arquitectura del Sistema)
Visión lógica de cómo interactúan las capas del sistema.

```mermaid
graph TB
    subgraph Frontend [React + Vite]
        UI[Componentes UI]
        Zustand[Zustand Store]
        Query[TanStack Query]
    end

    subgraph Backend [FastAPI]
        API[API Routers]
        Auth[Security/Auth]
        Worker[Queue Worker]
        DB[(SQLite WAL)]
        EB[Event Bus SSE]
    end

    subgraph Externo
        YTDLP[yt-dlp]
        SMB[Red Local / SMB Share]
    end

    UI --> API
    API --> Auth
    Auth --> DB
    API --> DB
    API --> EB
    EB -. SSE .-> Query
    Worker --> DB
    Worker --> YTDLP
    Worker --> SMB
```
