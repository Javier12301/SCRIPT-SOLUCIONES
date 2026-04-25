from __future__ import annotations

import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from transcribe_audio import OutputConfig, SegmentData, slugify, subtitle_ts, unique_dir_path, write_outputs


@contextmanager
def workspace_tempdir():
    with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
        yield Path(tmp)


class TranscribeAudioUtilsTests(unittest.TestCase):
    def test_slugify(self) -> None:
        self.assertEqual(slugify("Clase 1: Introduccion"), "clase-1-introduccion")
        self.assertEqual(slugify("   "), "audio")

    def test_subtitle_ts(self) -> None:
        self.assertEqual(subtitle_ts(1.23, for_vtt=False), "00:00:01,230")
        self.assertEqual(subtitle_ts(1.23, for_vtt=True), "00:00:01.230")

    def test_unique_dir_path(self) -> None:
        with workspace_tempdir() as root:
            (root / "audio").mkdir()
            self.assertEqual(unique_dir_path(root, "audio"), root / "audio_1")

    def test_write_outputs_complete_only(self) -> None:
        with workspace_tempdir() as out_dir:
            segments = [
                SegmentData(start=0.0, end=3.0, text="Hola"),
                SegmentData(start=3.0, end=6.0, text="Mundo"),
            ]
            files, chunks = write_outputs(
                output_dir=out_dir,
                stem="clase",
                segments=segments,
                output_config=OutputConfig(output_format="txt", split_mode="auto", parts_enabled=False),
            )
            self.assertEqual(chunks, 0)
            self.assertEqual(len(files), 1)
            self.assertTrue((out_dir / "clase_completo.txt").exists())

    def test_write_outputs_with_parts_and_subtitles(self) -> None:
        with workspace_tempdir() as out_dir:
            segments = [
                SegmentData(start=0.0, end=2.0, text="A"),
                SegmentData(start=2.0, end=4.0, text="B"),
                SegmentData(start=4.0, end=7.0, text="C"),
            ]
            files, chunks = write_outputs(
                output_dir=out_dir,
                stem="clase",
                segments=segments,
                output_config=OutputConfig(
                    output_format="txt",
                    split_mode="minutes",
                    max_minutes=0.05,
                    parts_enabled=True,
                    subtitle_formats={"srt", "vtt"},
                ),
            )
            self.assertGreaterEqual(chunks, 1)
            generated = {path.suffix for path in files}
            self.assertIn(".txt", generated)
            self.assertIn(".srt", generated)
            self.assertIn(".vtt", generated)


if __name__ == "__main__":
    unittest.main()
