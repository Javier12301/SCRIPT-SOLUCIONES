# Fase Planificacion - Estado de Implementacion

## Resumen
Se implemento la mayor parte del plan de optimizacion GUI-first, con foco en performance, lote de audios, robustez y nuevas salidas.

## Estado por fase

### Fase 1 - Refactor de nucleo y configuracion runtime
Estado: Completada
- Se agregaron `RuntimeConfig` y `OutputConfig`.
- Se separo la logica de runtime (`device`, `compute_type`, `beam`, `vad`, `batch_size`).
- Se mantuvo compatibilidad de `transcribe_audio(...)` para flujo unitario.

### Fase 2 - Performance real (audio largo + auto CPU/GPU)
Estado: Completada
- Se implemento `device_strategy="auto"` con fallback seguro de CUDA a CPU.
- Se incorporo `BatchedInferencePipeline` (modo `auto`/`batched`).
- Se exponen parametros VAD (`vad_filter`, `vad_parameters`, incluyendo `min_silence_duration_ms`).

### Fase 3 - Lote de audios y estructura de salida
Estado: Completada
- Se implemento `transcribe_audios_batch(...)`.
- La GUI ahora permite seleccionar multiples audios en cola.
- Se usa carpeta destino unica con subcarpeta por audio.
- Colisiones resueltas con sufijo incremental (`_1`, `_2`, ...).
- Errores por archivo no detienen todo el lote.

### Fase 4 - Politica de exportacion y subtitulos
Estado: Completada
- Se mantiene salida completa siempre.
- Se agrega opcion de partes independiente.
- Se agrega export opcional de subtitulos `.srt` y `.vtt`.

### Fase 5 - Robustez de memoria y concurrencia controlada
Estado: Completada
- Limpieza por archivo con `gc.collect()`.
- Limpieza CUDA condicional con `torch.cuda.empty_cache()` cuando aplica.
- Modo lote secuencial por defecto y paralelo limitado configurable.

### Fase 6 - QA, benchmark y release
Estado: Parcial
- Se agregaron pruebas unitarias basicas en `test_transcribe_audio.py`.
- Pendiente recomendado:
  - benchmark en hardware objetivo (CPU/GPU reales),
  - smoke test manual de GUI en entorno virtual del usuario final,
  - checklist final de release (versionado y empaquetado).

## Archivos principales modificados
- `transcribe_audio.py`
- `transcribe_audio_gui.py`
- `test_transcribe_audio.py`

## Ajustes posteriores de UX
Estado: Completado
- Se agrego scroll vertical general a la interfaz para que el formulario completo sea accesible en pantallas chicas o cuando se despliegan opciones avanzadas.
- Se deshabilitan visualmente las opciones de division cuando `Generar transcripcion por partes` no esta marcado.

## Ajustes de ayuda y proteccion
Estado: Completado
- Se agregaron helpers tipo tooltip en cada opcion avanzada para explicar modelo, hardware, compute, motor, beam, batch, VAD y paralelismo.
- El selector de modelo usa nombres amigables y mantiene mapeo interno hacia los identificadores reales de faster-whisper.
- Se agregaron guardrails antes de iniciar para limitar combinaciones pesadas y advertir configuraciones exigentes.
- Se agrego mensaje amigable para errores de memoria/CUDA con recomendaciones concretas.
