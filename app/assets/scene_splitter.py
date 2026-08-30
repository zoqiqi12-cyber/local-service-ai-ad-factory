from __future__ import annotations

import json
import subprocess
from pathlib import Path

from app.models.domain import AssetShot


class FFmpegSceneSplitter:
    """Detects scene boundaries with FFmpeg and returns coarse AssetShot records.

    This is intentionally label-free: later AI/vision analysis can enrich the shots
    without changing the split contract.
    """

    def __init__(self, threshold: float = 0.32, min_duration: float = 0.35) -> None:
        self.threshold = threshold
        self.min_duration = min_duration

    def split(self, video_path: str | Path) -> list[AssetShot]:
        video = Path(video_path)
        duration = self._duration(video)
        cuts = self._scene_times(video)
        points = [0.0, *[t for t in cuts if 0 < t < duration], duration]
        shots: list[AssetShot] = []
        for i, (start, end) in enumerate(zip(points, points[1:])):
            if end - start < self.min_duration:
                continue
            shots.append(
                AssetShot(
                    id=f"{video.stem}-{i:04d}",
                    source_file=str(video),
                    start=round(start, 3),
                    end=round(end, 3),
                    quality_score=50,
                )
            )
        return shots

    @staticmethod
    def _duration(video: Path) -> float:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "json", str(video),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        return float(payload["format"]["duration"])

    def _scene_times(self, video: Path) -> list[float]:
        expr = f"select='gt(scene,{self.threshold})',showinfo"
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-i", str(video), "-vf", expr, "-an", "-f", "null", "-"],
            capture_output=True,
            text=True,
        )
        times: list[float] = []
        for line in result.stderr.splitlines():
            marker = "pts_time:"
            if marker not in line:
                continue
            raw = line.split(marker, 1)[1].split()[0]
            try:
                times.append(float(raw))
            except ValueError:
                pass
        return sorted(set(times))
