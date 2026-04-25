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


class DownloaderService:
    def download(
        self,
        *,
        source_url: str,
        output_template: str,
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
