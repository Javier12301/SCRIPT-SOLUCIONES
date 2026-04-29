from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yt_dlp


@dataclass
class DownloadResult:
    output_path: str
    metadata: dict[str, Any]


@dataclass
class ResolvedSource:
    source_url: str
    title: str | None = None


class DownloaderService:
    def resolve_sources(self, source_url: str, *, ytdlp_options: dict[str, Any] | None = None) -> list[ResolvedSource]:
        options: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": "in_playlist",
        }
        if ytdlp_options:
            options.update(ytdlp_options)

        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(source_url, download=False)

        entries = info.get("entries") if isinstance(info, dict) else None
        if isinstance(entries, list) and entries:
            resolved_entries: list[ResolvedSource] = []
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                entry_url = (
                    entry.get("webpage_url")
                    or entry.get("original_url")
                    or entry.get("url")
                )
                if isinstance(entry_url, str) and entry_url:
                    resolved_entries.append(
                        ResolvedSource(
                            source_url=entry_url,
                            title=entry.get("title") if isinstance(entry.get("title"), str) else None,
                        )
                    )
            if resolved_entries:
                return resolved_entries

        return [ResolvedSource(source_url=source_url, title=info.get("title") if isinstance(info, dict) else None)]

    def download(
        self,
        *,
        source_url: str,
        output_template: str,
        ytdlp_options: dict[str, Any] | None = None,
        progress_hook: Callable[[dict[str, Any]], None] | None = None,
        postprocessor_hook: Callable[[dict[str, Any]], None] | None = None,
    ) -> DownloadResult:
        ydl_options: dict[str, Any] = {
            "outtmpl": output_template,
            "noplaylist": False,
            "restrictfilenames": False,
            "quiet": True,
            "no_warnings": True,
        }
        if ytdlp_options:
            ydl_options.update(ytdlp_options)

        if progress_hook is not None:
            ydl_options["progress_hooks"] = [progress_hook]
        if postprocessor_hook is not None:
            ydl_options["postprocessor_hooks"] = [postprocessor_hook]

        with yt_dlp.YoutubeDL(ydl_options) as ydl:
            info = ydl.extract_info(source_url, download=True)
            downloaded_path = self._resolve_output_path(info)
            return DownloadResult(output_path=downloaded_path, metadata=info)

    @staticmethod
    def _resolve_output_path(info: dict[str, Any]) -> str:
        requested = info.get("requested_downloads")
        if isinstance(requested, list) and requested:
            first = requested[0]
            path_value = first.get("filepath")
            if isinstance(path_value, str) and path_value:
                return str(Path(path_value))

        filepath = info.get("_filename")
        if isinstance(filepath, str) and filepath:
            return str(Path(filepath))

        raise RuntimeError("yt_dlp did not return an output path")
