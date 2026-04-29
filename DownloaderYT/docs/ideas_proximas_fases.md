# Ideas Proximas Fases - DownloaderYT

Documento de lluvia de ideas para evolucionar el sistema luego del backend basico (Fase 5).

## 1) Integracion Google Drive

Objetivo:
- Subir archivos completados automaticamente a Google Drive.

Ideas de implementacion:
- OAuth2 por usuario (cada usuario conecta su cuenta de Drive).
- Opcion por job: `delivery_targets.drive.enabled=true`.
- Carpeta destino configurable por usuario.
- Estado nuevo opcional por item: `uploading_drive`, `uploaded_drive`, `upload_failed`.
- Guardar `drive_file_id` y URL de comparticion.

Riesgos/consideraciones:
- Manejo de refresh tokens.
- Cuotas de API y limites por dia.
- Reintentos con backoff en errores 429/5xx.

## 2) Envio por WhatsApp como Documento

Objetivo:
- Enviar items completados por WhatsApp como documento.

Realidad tecnica:
- No existe API oficial de WhatsApp personal para automatizar envio libremente.
- Camino robusto: WhatsApp Business API (Meta/Proveedor BSP).

Ideas de implementacion:
- Adaptador de envio `delivery_targets.whatsapp`.
- Config por usuario: numero destino, proveedor, credenciales.
- Envio como `document` para mantener archivo original.
- Estados por item: `sending_whatsapp`, `sent_whatsapp`, `whatsapp_failed`.

Riesgos/consideraciones:
- Costos por conversacion en WhatsApp Business.
- Politicas de plantillas y ventanas de mensajeria.
- Dependencia de proveedor externo.

## 3) Otras recomendaciones (priorizadas)

### Prioridad Alta

1. Cola de tareas real (RQ/Celery/Arq) + worker separado.
- Mejora resiliencia, reinicios y escalado.

2. Limites y cuotas por usuario.
- Max jobs activos, max items por playlist, max tamano, anti-abuso.

3. Limpieza automatica de archivos.
- Retencion por dias y GC de temporales/orfanos.

4. Observabilidad.
- Logs estructurados, metricas basicas, dashboard de salud de workers.

### Prioridad Media

1. Presets de calidad/formato.
- `video_1080_mp4`, `audio_mp3_320`, `audio_opus`, etc.

2. UI/UX de progreso mejorado.
- ETA total del job, velocidad agregada, historico de errores.

3. Webhooks.
- Notificar frontend/app externa al completar/fallar item.

4. Historial de entrega.
- Registro unificado de download + transfer + envio (Drive/WhatsApp).

### Prioridad Baja

1. Multi-plataforma de origen.
- Vimeo/TikTok/Twitch con reglas por extractor.

2. Deduplicacion por hash.
- Evitar bajar mismo archivo varias veces.

3. Mini motor de reglas.
- Ejemplo: "si dura > X min, extraer solo audio".

## 4) Propuesta de orden de ejecucion

1. Cola robusta + observabilidad.
2. Delivery a Google Drive.
3. Sistema de delivery abstraido (targets).
4. WhatsApp Business como target adicional.
5. Presets avanzados y reglas.

## 5) Nota de arquitectura sugerida

Para no acoplar todo al worker actual, conviene separar:
- `download_pipeline` (obtencion y conversion)
- `delivery_pipeline` (Drive, WhatsApp, SMB, futuros destinos)
- `retry_policy` comun reutilizable por etapa.

Asi el frontend puede mostrar progreso por etapa y no solo por descarga.
