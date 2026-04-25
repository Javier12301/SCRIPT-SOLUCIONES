from __future__ import annotations

import argparse
import gc
import math
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal

OutputFormat = Literal["txt", "md"]
SplitMode = Literal["none", "auto", "minutes"]
SubtitleFormat = Literal["srt", "vtt"]
DeviceStrategy = Literal["auto", "cpu", "cuda"]
ComputeType = Literal["auto", "int8", "float16", "int8_float16", "float32"]
InferenceEngine = Literal["auto", "standard", "batched"]
BatchMode = Literal["sequential", "parallel"]


def format_ts(seconds: float) -> str:
    total = max(0, int(seconds))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "audio"


@dataclass
class SegmentData:
    start: float
    end: float
    text: str


@dataclass
class TranscriptionResult:
    audio_path: Path
    language: str = ""
    language_probability: float = 0.0
    duration_seconds: int = 0
    segment_count: int = 0
    output_dir: Path = Path(".")
    chunk_count: int = 0
    files_written: list[Path] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    used_device: str = ""
    used_compute_type: str = ""
    success: bool = True
    error_message: str | None = None


@dataclass
class BatchTranscriptionResult:
    total_count: int
    success_count: int
    failed_count: int
    results: list[TranscriptionResult]


MEMORY_ERROR_HINT = (
    "No alcanzo la memoria para esta configuracion. Proba bajar el modelo, "
    "reducir Batch size, usar modo secuencial o dejar Hardware/Compute en auto."
)


@dataclass
class RuntimeConfig:
    model_name: str = "small"
    language: str = "es"
    device_strategy: DeviceStrategy = "auto"
    compute_type: ComputeType = "auto"
    beam_size: int = 2
    vad_filter: bool = True
    vad_parameters: dict[str, int | float] = field(default_factory=lambda: {"min_silence_duration_ms": 500})
    inference_engine: InferenceEngine = "auto"
    batch_size: int = 4
    cpu_threads: int | None = None
    num_workers: int = 1


@dataclass
class OutputConfig:
    output_format: OutputFormat = "txt"
    split_mode: SplitMode = "auto"
    max_chars: int = 2500
    max_minutes: float = 2.5
    parts_enabled: bool = True
    subtitle_formats: set[SubtitleFormat] = field(default_factory=set)


@dataclass
class _RuntimeBundle:
    model: Any
    pipeline: Any | None
    device: str
    compute_type: str
    use_batched: bool


def chunk_segments(
    segments: list[SegmentData],
    max_chars: int,
    max_minutes: float,
) -> list[list[SegmentData]]:
    chunks: list[list[SegmentData]] = []
    current: list[SegmentData] = []
    current_chars = 0
    current_start = 0.0

    for segment in segments:
        seg_chars = len(segment.text) + 32
        if not current:
            current_start = segment.start

        exceeds_chars = current and current_chars + seg_chars > max_chars
        exceeds_minutes = current and (segment.end - current_start) > max_minutes * 60

        if exceeds_chars or exceeds_minutes:
            chunks.append(current)
            current = []
            current_chars = 0
            current_start = segment.start

        current.append(segment)
        current_chars += seg_chars

    if current:
        chunks.append(current)

    return chunks


def build_markdown_lines(title: str, body_lines: list[str], subtitle: str | None = None) -> list[str]:
    lines = [f"# {title}", ""]
    if subtitle:
        lines.extend([subtitle, ""])
    lines.extend(body_lines)
    return lines


def build_text_lines(title: str | None, body_lines: list[str]) -> list[str]:
    lines: list[str] = []
    if title:
        lines.extend([title, ""])
    lines.extend(body_lines)
    return lines


def write_text_file(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def subtitle_ts(seconds: float, for_vtt: bool) -> str:
    total_ms = max(0, int(round(seconds * 1000)))
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)
    separator = "." if for_vtt else ","
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{separator}{ms:03d}"


def write_subtitle_file(
    output_dir: Path,
    file_stem: str,
    segments: list[SegmentData],
    subtitle_format: SubtitleFormat,
) -> Path:
    output_path = output_dir / f"{file_stem}.{subtitle_format}"
    lines: list[str] = []
    if subtitle_format == "vtt":
        lines.extend(["WEBVTT", ""])
    for index, segment in enumerate(segments, start=1):
        start_ts = subtitle_ts(segment.start, for_vtt=subtitle_format == "vtt")
        end_ts = subtitle_ts(segment.end, for_vtt=subtitle_format == "vtt")
        lines.append(str(index))
        lines.append(f"{start_ts} --> {end_ts}")
        lines.append(segment.text)
        lines.append("")
    write_text_file(output_path, lines)
    return output_path


def unique_dir_path(base_dir: Path, desired_name: str) -> Path:
    candidate = base_dir / desired_name
    if not candidate.exists():
        return candidate
    index = 1
    while True:
        new_candidate = base_dir / f"{desired_name}_{index}"
        if not new_candidate.exists():
            return new_candidate
        index += 1


def write_segment_file(
    output_dir: Path,
    file_stem: str,
    title: str,
    subtitle: str | None,
    body_lines: list[str],
    output_format: OutputFormat,
) -> Path:
    extension = "md" if output_format == "md" else "txt"
    file_path = output_dir / f"{file_stem}.{extension}"

    if output_format == "md":
        lines = build_markdown_lines(title, [f"- {line}" for line in body_lines], subtitle=subtitle)
    else:
        txt_title = title if subtitle is None else f"{title} ({subtitle})"
        lines = build_text_lines(txt_title if file_stem.endswith("completo") is False else None, body_lines)

    write_text_file(file_path, lines)
    return file_path


def write_outputs(
    output_dir: Path,
    stem: str,
    segments: list[SegmentData],
    output_config: OutputConfig,
) -> tuple[list[Path], int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    files_written: list[Path] = []

    full_lines = [f"[{format_ts(seg.start)} - {format_ts(seg.end)}] {seg.text}" for seg in segments]
    files_written.append(
        write_segment_file(
            output_dir=output_dir,
            file_stem=f"{stem}_completo",
            title="Transcripcion completa",
            subtitle=None,
            body_lines=full_lines,
            output_format=output_config.output_format,
        )
    )

    chunk_count = 0
    if output_config.parts_enabled and output_config.split_mode != "none":
        effective_minutes = output_config.max_minutes if output_config.split_mode == "minutes" else 2.5
        effective_chars = output_config.max_chars if output_config.split_mode == "auto" else 10**9
        chunks = chunk_segments(segments, max_chars=effective_chars, max_minutes=effective_minutes)
        chunk_count = len(chunks)
        width = max(2, len(str(chunk_count)))

        for index, chunk in enumerate(chunks, start=1):
            start_ts = format_ts(chunk[0].start)
            end_ts = format_ts(chunk[-1].end)
            prefix = f"{stem}_parte_{index:0{width}d}"
            chunk_lines = [f"[{format_ts(seg.start)} - {format_ts(seg.end)}] {seg.text}" for seg in chunk]
            files_written.append(
                write_segment_file(
                    output_dir=output_dir,
                    file_stem=prefix,
                    title=f"Parte {index}",
                    subtitle=f"{start_ts} - {end_ts}",
                    body_lines=chunk_lines,
                    output_format=output_config.output_format,
                )
            )

    for subtitle_format in sorted(output_config.subtitle_formats):
        files_written.append(
            write_subtitle_file(
                output_dir=output_dir,
                file_stem=f"{stem}_completo",
                segments=segments,
                subtitle_format=subtitle_format,
            )
        )

    return files_written, chunk_count


def _import_runtime_classes() -> tuple[Any, Any]:
    from faster_whisper import BatchedInferencePipeline, WhisperModel

    return WhisperModel, BatchedInferencePipeline


def _resolve_compute_type(device: str, compute_type: ComputeType) -> str:
    if compute_type != "auto":
        return compute_type
    return "float16" if device == "cuda" else "int8"


def _build_runtime(runtime_config: RuntimeConfig) -> _RuntimeBundle:
    WhisperModel, BatchedInferencePipeline = _import_runtime_classes()
    common_params: dict[str, Any] = {
        "num_workers": runtime_config.num_workers,
    }
    if runtime_config.cpu_threads is not None:
        common_params["cpu_threads"] = runtime_config.cpu_threads

    def build_on(device: str) -> _RuntimeBundle:
        resolved_compute = _resolve_compute_type(device, runtime_config.compute_type)
        model = WhisperModel(
            runtime_config.model_name,
            device=device,
            compute_type=resolved_compute,
            **common_params,
        )
        use_batched = runtime_config.inference_engine == "batched" or runtime_config.inference_engine == "auto"
        pipeline = BatchedInferencePipeline(model=model) if use_batched else None
        return _RuntimeBundle(
            model=model,
            pipeline=pipeline,
            device=device,
            compute_type=resolved_compute,
            use_batched=use_batched,
        )

    if runtime_config.device_strategy == "cpu":
        return build_on("cpu")
    if runtime_config.device_strategy == "cuda":
        return build_on("cuda")

    try:
        return build_on("cuda")
    except Exception:
        return build_on("cpu")


def _cleanup_memory(used_device: str) -> None:
    gc.collect()
    if used_device != "cuda":
        return
    try:
        import torch  # type: ignore

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        return


def is_memory_error(exc: Exception) -> bool:
    text = str(exc).lower()
    markers = (
        "out of memory",
        "cuda",
        "allocation",
        "allocate",
        "not enough memory",
        "cublas",
        "cudnn",
        "failed to alloc",
        "memory",
        "vram",
    )
    return any(marker in text for marker in markers)


def friendly_error_message(exc: Exception) -> str:
    if is_memory_error(exc):
        return MEMORY_ERROR_HINT
    return str(exc)


def _transcribe_with_runtime(
    runtime: _RuntimeBundle,
    audio_path: Path,
    output_dir: Path,
    output_config: OutputConfig,
    runtime_config: RuntimeConfig,
) -> TranscriptionResult:
    started = time.perf_counter()
    kwargs: dict[str, Any] = {
        "language": runtime_config.language,
        "beam_size": runtime_config.beam_size,
        "vad_filter": runtime_config.vad_filter,
    }
    if runtime_config.vad_filter and runtime_config.vad_parameters:
        kwargs["vad_parameters"] = runtime_config.vad_parameters

    if runtime.use_batched and runtime.pipeline is not None:
        transcript, info = runtime.pipeline.transcribe(
            str(audio_path),
            batch_size=runtime_config.batch_size,
            **kwargs,
        )
    else:
        transcript, info = runtime.model.transcribe(
            str(audio_path),
            **kwargs,
        )

    segments: list[SegmentData] = []
    for item in transcript:
        text = item.text.strip()
        if not text:
            continue
        segments.append(SegmentData(start=item.start, end=item.end, text=text))

    if not segments:
        raise RuntimeError("No se pudo extraer texto del audio.")

    stem = slugify(audio_path.stem)
    files_written, chunk_count = write_outputs(
        output_dir=output_dir,
        stem=stem,
        segments=segments,
        output_config=output_config,
    )

    elapsed = time.perf_counter() - started
    total_duration = math.ceil(segments[-1].end - segments[0].start)
    return TranscriptionResult(
        audio_path=audio_path,
        language=info.language,
        language_probability=info.language_probability,
        duration_seconds=total_duration,
        segment_count=len(segments),
        output_dir=output_dir,
        chunk_count=chunk_count,
        files_written=files_written,
        elapsed_seconds=elapsed,
        used_device=runtime.device,
        used_compute_type=runtime.compute_type,
    )


def _run_single_audio(
    audio_path: Path,
    output_dir: Path,
    runtime_config: RuntimeConfig,
    output_config: OutputConfig,
    runtime: _RuntimeBundle | None = None,
) -> TranscriptionResult:
    bundle = runtime or _build_runtime(runtime_config)
    try:
        return _transcribe_with_runtime(
            runtime=bundle,
            audio_path=audio_path,
            output_dir=output_dir,
            output_config=output_config,
            runtime_config=runtime_config,
        )
    finally:
        _cleanup_memory(bundle.device)


def transcribe_audio(
    audio_path: Path,
    output_dir: Path,
    model_name: str = "small",
    language: str = "es",
    split_mode: SplitMode = "auto",
    output_format: OutputFormat = "txt",
    max_chars: int = 2500,
    max_minutes: float = 2.5,
    parts_enabled: bool = True,
    subtitle_formats: set[SubtitleFormat] | None = None,
    runtime_config: RuntimeConfig | None = None,
    output_config: OutputConfig | None = None,
) -> TranscriptionResult:
    audio_path = audio_path.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()

    runtime_cfg = runtime_config or RuntimeConfig(
        model_name=model_name,
        language=language,
    )
    output_cfg = output_config or OutputConfig(
        output_format=output_format,
        split_mode=split_mode,
        max_chars=max_chars,
        max_minutes=max_minutes,
        parts_enabled=parts_enabled,
        subtitle_formats=subtitle_formats or set(),
    )
    return _run_single_audio(
        audio_path=audio_path,
        output_dir=output_dir,
        runtime_config=runtime_cfg,
        output_config=output_cfg,
    )


def transcribe_audios_batch(
    audio_paths: list[Path],
    destination_root: Path,
    runtime_config: RuntimeConfig | None = None,
    output_config: OutputConfig | None = None,
    mode: BatchMode = "sequential",
    max_parallel_workers: int = 2,
    progress_callback: Callable[[str], None] | None = None,
) -> BatchTranscriptionResult:
    if not audio_paths:
        raise ValueError("No hay audios para transcribir.")

    destination_root = destination_root.expanduser().resolve()
    destination_root.mkdir(parents=True, exist_ok=True)
    runtime_cfg = runtime_config or RuntimeConfig()
    output_cfg = output_config or OutputConfig()
    results: list[TranscriptionResult] = []

    def notify(message: str) -> None:
        if progress_callback:
            progress_callback(message)

    def run_one(index: int, audio_path: Path, shared_runtime: _RuntimeBundle | None = None) -> TranscriptionResult:
        resolved_audio = audio_path.expanduser().resolve()
        target_dir = unique_dir_path(destination_root, slugify(resolved_audio.stem))
        notify(f"[{index + 1}/{len(audio_paths)}] Iniciando: {resolved_audio.name}")
        try:
            result = _run_single_audio(
                audio_path=resolved_audio,
                output_dir=target_dir,
                runtime_config=runtime_cfg,
                output_config=output_cfg,
                runtime=shared_runtime,
            )
            notify(f"[{index + 1}/{len(audio_paths)}] OK: {resolved_audio.name}")
            return result
        except Exception as exc:
            error_message = friendly_error_message(exc)
            notify(f"[{index + 1}/{len(audio_paths)}] Error: {resolved_audio.name} -> {error_message}")
            return TranscriptionResult(
                audio_path=resolved_audio,
                output_dir=target_dir,
                success=False,
                error_message=error_message,
            )

    if mode == "parallel" and max_parallel_workers > 1:
        with ThreadPoolExecutor(max_workers=max_parallel_workers) as executor:
            future_map = {executor.submit(run_one, idx, path, None): idx for idx, path in enumerate(audio_paths)}
            ordered: dict[int, TranscriptionResult] = {}
            for future in as_completed(future_map):
                idx = future_map[future]
                ordered[idx] = future.result()
            for idx in range(len(audio_paths)):
                results.append(ordered[idx])
    else:
        shared_runtime = _build_runtime(runtime_cfg)
        for index, audio_path in enumerate(audio_paths):
            results.append(run_one(index, audio_path, shared_runtime=shared_runtime))

    success_count = sum(1 for item in results if item.success)
    failed_count = len(results) - success_count
    return BatchTranscriptionResult(
        total_count=len(results),
        success_count=success_count,
        failed_count=failed_count,
        results=results,
    )

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transcribe un audio y lo guarda en txt o md.")
    parser.add_argument("audio_path", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("transcripcion_salida"))
    parser.add_argument("--model", default="small")
    parser.add_argument("--language", default="es")
    parser.add_argument("--max-chars", type=int, default=2500)
    parser.add_argument("--max-minutes", type=float, default=2.5)
    parser.add_argument("--format", choices=("txt", "md"), default="txt")
    parser.add_argument("--split-mode", choices=("none", "auto", "minutes"), default="auto")
    parser.add_argument("--parts-enabled", action="store_true")
    parser.add_argument("--subtitle", choices=("srt", "vtt"), action="append", default=[])
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--compute-type", choices=("auto", "int8", "float16", "int8_float16", "float32"), default="auto")
    parser.add_argument("--engine", choices=("auto", "standard", "batched"), default="auto")
    parser.add_argument("--beam-size", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=4)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = transcribe_audio(
        audio_path=args.audio_path,
        output_dir=args.output_dir,
        model_name=args.model,
        language=args.language,
        split_mode=args.split_mode,
        output_format=args.format,
        max_chars=args.max_chars,
        max_minutes=args.max_minutes,
        parts_enabled=args.parts_enabled or args.split_mode != "none",
        subtitle_formats=set(args.subtitle),
        runtime_config=RuntimeConfig(
            model_name=args.model,
            language=args.language,
            device_strategy=args.device,
            compute_type=args.compute_type,
            beam_size=args.beam_size,
            inference_engine=args.engine,
            batch_size=args.batch_size,
        ),
    )

    print(f"Idioma detectado: {result.language} ({result.language_probability:.2%})")
    print(f"Duracion transcripta: {result.duration_seconds} segundos")
    print(f"Segmentos: {result.segment_count}")
    print(f"Partes creadas: {result.chunk_count}")
    print(f"Device: {result.used_device} / Compute: {result.used_compute_type}")
    print(f"Tiempo: {result.elapsed_seconds:.2f}s")
    print(f"Salida: {result.output_dir}")


if __name__ == "__main__":
    main()
