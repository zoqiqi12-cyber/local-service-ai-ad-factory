from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from app.models.domain import Timeline


class FFmpegRenderer:
    """Renders real timeline clips to a vertical MP4 using FFmpeg.

    AI-pending clips must be resolved to local files before rendering. V1 keeps the
    renderer deterministic and provider-agnostic.
    """

    def render(self, timeline: Timeline, output_file: str | Path) -> Path:
        unresolved = [c for c in timeline.clips if c.source_type == "ai_pending"]
        if unresolved:
            raise ValueError(f"Timeline contains {len(unresolved)} unresolved AI clips")

        output = Path(output_file).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix="ad-factory-") as temp_dir:
            temp = Path(temp_dir)
            rendered_parts: list[Path] = []
            for index, clip in enumerate(timeline.clips):
                if not clip.source_file:
                    raise ValueError(f"Clip {index} has no source_file")
                start = clip.source_start or 0.0
                end = clip.source_end or start + (clip.timeline_end - clip.timeline_start)
                duration = max(0.1, end - start)
                part = temp / f"part-{index:04d}.mp4"
                command = [
                    "ffmpeg", "-y",
                    "-ss", f"{start:.3f}",
                    "-t", f"{duration:.3f}",
                    "-i", clip.source_file,
                    "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30",
                    "-an",
                    "-c:v", "libx264",
                    "-preset", "veryfast",
                    "-crf", "20",
                    str(part),
                ]
                self._run(command)
                rendered_parts.append(part)

            concat_file = temp / "concat.txt"
            concat_file.write_text(
                "\n".join(f"file '{part.as_posix()}'" for part in rendered_parts),
                encoding="utf-8",
            )
            self._run([
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", str(concat_file), "-c", "copy", str(output),
            ])
        return output

    @staticmethod
    def _run(command: list[str]) -> None:
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except FileNotFoundError as exc:
            raise RuntimeError("FFmpeg/ffprobe 未安装或不在 PATH 中") from exc
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(exc.stderr[-2000:] if exc.stderr else "FFmpeg render failed") from exc
