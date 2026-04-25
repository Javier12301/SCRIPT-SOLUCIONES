# Script Personales

Repositorio para centralizar automatizaciones personales orientadas a productividad y estudio.

## Estado del repositorio

### Disponible hoy
- `Transcriptor Audios`: transcripción local de audio (sin servicios externos), con:
  - GUI para usuarios no técnicos
  - CLI para automatización
  - salida en `txt`/`md`
  - división opcional en partes
  - export opcional a subtítulos `srt` y `vtt`
  - procesamiento por lote (múltiples audios)

---

## Estructura actual

```text
.
├─ Transcriptor Audios/
│  ├─ transcribe_audio.py          # Núcleo (CLI + lógica de transcripción)
│  ├─ transcribe_audio_gui.py      # Interfaz gráfica (Tkinter)
│  ├─ abrir_transcriptor.bat       # Lanzador de GUI en Windows
│  ├─ requirements.txt             # Dependencias del módulo
│  ├─ memoria_contexto.md          # Memoria funcional/técnica
│  ├─ fase_planificacion.md        # Estado de implementación por fases
│  └─ test_transcribe_audio.py     # Tests unitarios básicos
└─ .gitignore
```

---

## Requisitos

- Python 3.10+
- Windows recomendado para uso con `.bat`
- Dependencias del módulo de transcriptor:
  ```bash
  pip install -r "Transcriptor Audios/requirements.txt"
  ```

---

## Transcriptor de Audios (GUI)

Archivo principal: `Transcriptor Audios/transcribe_audio_gui.py`

### Qué hace
- Permite cargar uno o varios audios (`mp3`, `wav`, `m4a`, `mp4`, `aac`, `ogg`, `flac`)
- Procesa por lote
- Crea siempre un archivo completo por audio
- Opcionalmente crea partes y subtítulos

### Cómo abrirlo

#### Opción 1 (Windows, rápida)
```bat
Transcriptor Audios\abrir_transcriptor.bat
```

#### Opción 2 (directo con Python)
```bash
python "Transcriptor Audios/transcribe_audio_gui.py"
```

---

## Guía de uso de `transcribe_audio_gui.py`

1. En **Audios**, hacé clic en **Agregar audios** y seleccioná uno o varios archivos.
2. En **Salida**, elegí la carpeta donde querés guardar resultados.
3. En **Formato**, elegí `txt` o `md`.
4. En **Partes**:
   - Activado: además del completo, genera archivos por partes.
   - Modos:
     - `Sin división`: solo completo (aunque partes esté activo no fragmenta)
     - `Automática`: divide por lógica interna (caracteres + ventana temporal)
     - `Por minutos`: divide por minutos fijos (ej. 10)
5. (Opcional) Marcá subtítulos `SRT` y/o `VTT`.
6. (Opcional) Activá **Mostrar opciones avanzadas** si necesitás ajustar modelo, hardware o rendimiento.
7. Clic en **Transcribir lote**.
8. Revisá el panel **Progreso** para estado, logs y resumen final (éxitos/fallos).

---

## Opciones avanzadas (resumen rápido)

- **Modelo**: `tiny`, `base`, `small`, `medium`, `large-v3`, `turbo`
- **Hardware**: `auto` (recomendado), `cpu`, `cuda`
- **Compute**: `auto` (recomendado), `int8`, `float16`, etc.
- **Motor**: `auto`, `standard`, `batched`
- **Beam size**: más alto puede mejorar algo, pero demora más
- **Batch size**: más alto puede acelerar, pero consume más memoria
- **VAD activo**: saltea silencios
- **Modo de lote**:
  - `sequential` (más estable)
  - `parallel` (más rápido, más consumo)

> Recomendado para no técnicos: `small`, `auto/auto/auto`, `beam 2`, `batch 4`, `sequential`.

---

## Salidas generadas

Por cada audio, se crea una subcarpeta dentro del destino elegido.

Ejemplo:
```text
transcripciones/
└─ clase-1-introduccion/
   ├─ clase-1-introduccion_completo.txt
   ├─ clase-1-introduccion_parte_01.txt
   ├─ clase-1-introduccion_parte_02.txt
   ├─ clase-1-introduccion_completo.srt
   └─ clase-1-introduccion_completo.vtt
```

---

## Uso por CLI (opcional)

```bash
python "Transcriptor Audios/transcribe_audio.py" "ruta/al/audio.mp3" --format txt --split-mode auto
```

Ejemplo por minutos:
```bash
python "Transcriptor Audios/transcribe_audio.py" "ruta/al/audio.mp3" --split-mode minutes --max-minutes 10 --format md --subtitle srt --subtitle vtt
```

---

## Testing básico

```bash
python "Transcriptor Audios/test_transcribe_audio.py"
```

---

## Notas importantes

- El archivo `abrir_transcriptor.bat` usa una ruta fija de Python; puede requerir ajuste según tu PC.
- Si aparece error de memoria:
  - bajá el modelo
  - bajá `batch size`
  - usá modo `sequential`
  - dejá `hardware/compute` en `auto`
