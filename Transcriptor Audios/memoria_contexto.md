# Memoria de Contexto - Transcriptor Audios

## 1) Objetivo del proyecto
Este proyecto permite transcribir audios de estudio en local (sin servicios externos), usando Whisper a traves de `faster-whisper`.

Tiene dos formas de uso:
- Interfaz grafica (principal): seleccion de audio, formato de salida y modo de division.
- Script por linea de comandos (CLI): para automatizar o integrar en otros flujos.

## 2) Estructura actual
- `transcribe_audio.py`: nucleo de transcripcion y escritura de archivos.
- `transcribe_audio_gui.py`: interfaz `tkinter` para uso manual.
- `abrir_transcriptor.bat`: lanzador en Windows que abre la GUI con un Python runtime fijo.

## 3) Flujo funcional (alto nivel)
1. Usuario elige un archivo de audio y una carpeta de salida.
2. Se ejecuta `transcribe_audio(...)` con modelo Whisper (`small` por defecto, CPU/int8).
3. Se generan segmentos con timestamp `[inicio - fin] texto`.
4. Se escribe siempre un archivo completo.
5. Opcionalmente, se generan partes segun modo de division:
- `none`: no divide.
- `auto`: divide por limite de caracteres (2500) y ventana de tiempo de referencia.
- `minutes`: divide por minutos configurables por el usuario.
6. Se informa idioma detectado, duracion, segmentos y archivos generados.

## 4) Detalle tecnico por archivo

### `transcribe_audio.py`
- Define tipos:
  - `OutputFormat`: `txt | md`
  - `SplitMode`: `none | auto | minutes`
  - `SegmentData` y `TranscriptionResult`
- Utilidades:
  - `format_ts`: formatea segundos a `MM:SS` o `HH:MM:SS`
  - `slugify`: normaliza nombre base para archivos de salida
- Logica de division:
  - `chunk_segments`: crea bloques por caracteres y/o minutos
- Escritura de salida:
  - `write_outputs`: crea archivo `*_completo` y, si aplica, `*_parte_XX`
  - Formatos soportados:
    - `txt`: lineas planas
    - `md`: lista con bullets
- Funcion principal:
  - `transcribe_audio(...)`: instancia `WhisperModel`, ejecuta transcripcion y devuelve `TranscriptionResult`
- CLI:
  - Permite pasar ruta audio, formato, modo de split, limites de caracteres/minutos, idioma y modelo.

### `transcribe_audio_gui.py`
- App `TranscriptionApp` con:
  - selector de audio
  - selector de carpeta de salida
  - formato (`txt`, `md`)
  - split (`none`, `auto`, `minutes`) + input de minutos
  - area de log y estado
- Validaciones:
  - audio obligatorio y existente
  - carpeta de salida obligatoria
  - minutos validos si split por minutos
- Concurrencia:
  - ejecuta transcripcion en `threading.Thread` para no bloquear la UI
  - usa `root.after(...)` para actualizar UI de forma segura

### `abrir_transcriptor.bat`
- Busca un ejecutable Python en ruta fija:
  - `C:\Users\Lumi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`
- Si no existe, corta con mensaje.
- Si existe, ejecuta `transcribe_audio_gui.py`.

## 5) Entradas y salidas

### Entradas
- Archivos de audio: `mp3`, `wav`, `m4a`, `mp4`, `aac`, `ogg`, `flac`.
- Parametros de transcripcion:
  - idioma (default `es`)
  - modelo (default `small`)
  - formato de salida (`txt`/`md`)
  - modo de division

### Salidas
- Carpeta elegida por usuario (default GUI: `./transcripciones`).
- Archivos generados:
  - `<slug>_completo.txt|md`
  - `<slug>_parte_01.txt|md`, `<slug>_parte_02...` (si hay division)

## 6) Dependencias inferidas
- Python 3.10+ (uso de `|` en tipos y anotaciones modernas).
- `faster-whisper` (y dependencias nativas asociadas).
- Librerias estandar: `tkinter`, `pathlib`, `threading`, etc.

## 7) Supuestos y decisiones importantes
- Procesamiento en CPU (`device="cpu"`) y `compute_type="int8"` para compatibilidad/rendimiento en equipos comunes.
- Siempre se genera archivo completo aunque tambien haya partes.
- `split_mode="auto"` combina limite de caracteres con una referencia temporal interna.
- Si no se detecta texto util, se lanza error explicito.

## 8) Riesgos / mejoras recomendadas
- Ruta de Python hardcodeada en `.bat` (poco portable entre PCs/usuarios).
- Falta un `requirements.txt` o `pyproject.toml` para instalacion reproducible.
- Falta README con instrucciones de uso rapido.
- La GUI no expone seleccion de modelo/idioma (aunque el core lo soporta).
- No hay tests automatizados del core (`transcribe_audio.py`).

## 9) Comandos de uso rapido

### GUI
```bat
abrir_transcriptor.bat
```

### CLI
```bash
python transcribe_audio.py "ruta/al/audio.mp3" --format txt --split-mode auto
```

Ejemplo con division por minutos:
```bash
python transcribe_audio.py "ruta/al/audio.mp3" --split-mode minutes --max-minutes 10 --format md
```

