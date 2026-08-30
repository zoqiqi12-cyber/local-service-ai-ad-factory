from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from app.editing.renderer import FFmpegRenderer
from app.editing.subtitles import SubtitleBuilder
from app.models.domain import AdScript, Timeline


class FinalComposer:
    """Compose rendered picture, subtitles, voice and optional BGM into final MP4."""

    def __init__(self) -> None:
        self.renderer = FFmpegRenderer()
        self.subtitles = SubtitleBuilder()

    def compose(
        self,
        script: AdScript,
        timeline: Timeline,
        output_file: str | Path,
        voice_file: str | Path | None = None,
        music_file: str | Path | None = None,
        burn_subtitles: bool = True,
    ) -> Path:
        output = Path(output_file).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix="ad-factory-final-") as temp_dir:
            temp = Path(temp_dir)
            picture = self.renderer.render(timeline, temp / "picture.mp4")
            subtitle = self.subtitles.write(script, timeline, temp / "captions.srt")

            command = ["ffmpeg", "-y", "-i", str(picture)]
            input_index = 1
            voice_index: int | None = None
            music_index: int | None = None

            if voice_file:
                command += ["-i", str(Path(voice_file).expanduser().resolve())]
                voice_index = input_index
                input_index += 1
            if music_file:
                command += ["-stream_loop", "-1", "-i", str(Path(music_file).expanduser().resolve())]
                music_index = input_index

            filters: list[str] = []
            video_map = "0:v"
            if burn_subtitles:
                escaped = str(subtitle).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
                filters.append(
                    f"[0:v]subtitles='{escaped}':force_style='FontSize=18,Alignment=2,MarginV=170,Outline=2'[v]"
                )
                video_map = "[v]"

            audio_map: str | None = None
            if voice_index is not None and music_index is not None:
                filters.append(
                    f"[{music_index}:a]volume=0.12[bgm];"
                    f"[{voice_index}:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[a]"
                )
                audio_map = "[a]"
            elif voice_index is not None:
                audio_map = f"{voice_index}:a"
            elif music_index is not None:
                filters.append(f"[{music_index}:a]volume=0.16[a]")
                audio_map = "[a]"

            if filters:
                command += ["-filter_complex", ";".join(filters)]
            command += ["-map", video_map]
            if audio_map:
                command += ["-map", audio_map, "-c:a", "aac", "-b:a", "192k"]
            else:
                command += ["-an"]

            command += [
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "20",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                "-shortest",
                str(output),
            ]
            self._run(command)
        return output

    @staticmethod
    def _run(command: list[str]) -> None:
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except FileNotFoundError as exc:
            raise RuntimeError("FFmpeg 未安装或不在 PATH 中") from exc
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(exc.stderr[-3000:] if exc.stderr else "Final compose failed") from exc
