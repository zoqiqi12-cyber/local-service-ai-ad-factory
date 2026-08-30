from __future__ import annotations

import statistics
import subprocess
from pathlib import Path

from app.models.domain import AssetShot
from app.assets.visual_fingerprint import VisualFingerprintExtractor


class AssetVisualAnalyzer:
    """Cheap local visual scoring using a few tiny grayscale frames.

    This gives V1 useful motion/sharpness/quality signals without requiring a GPU
    or an external vision API. Scores are intentionally approximate and bounded
    0..100 so they can later be blended with a learned vision model.
    """

    width = 64
    height = 64

    def analyze(self, asset: AssetShot) -> AssetShot:
        frames = self._sample_frames(asset.source_file, asset.start, asset.end)
        if not frames:
            return asset

        sharpness = self._sharpness(frames)
        motion = self._motion(frames)
        exposure = self._exposure(frames)
        stability = max(0.0, min(100.0, 100.0 - motion * 0.65))
        quality = max(0.0, min(100.0, sharpness * 0.45 + exposure * 0.35 + stability * 0.20))
        fp = VisualFingerprintExtractor().extract(asset.source_file, asset.start, asset.end)

        return asset.model_copy(update={
            "sharpness_score": round(sharpness, 2),
            "motion_score": round(motion, 2),
            "stability_score": round(stability, 2),
            "quality_score": round(quality, 2),
            "visual_fingerprint": fp.value if fp else None,
        })

    def _sample_frames(self, source_file: str, start: float, end: float) -> list[bytes]:
        duration = max(0.2, end - start)
        frames: list[bytes] = []
        for ratio in (0.25, 0.5, 0.75):
            t = start + duration * ratio
            command = [
                "ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(Path(source_file)),
                "-frames:v", "1", "-vf", f"scale={self.width}:{self.height},format=gray",
                "-f", "rawvideo", "-",
            ]
            try:
                result = subprocess.run(command, check=True, capture_output=True)
            except (FileNotFoundError, subprocess.CalledProcessError):
                continue
            expected = self.width * self.height
            if len(result.stdout) >= expected:
                frames.append(result.stdout[:expected])
        return frames

    def _sharpness(self, frames: list[bytes]) -> float:
        values: list[float] = []
        w = self.width
        for frame in frames:
            diffs = []
            for y in range(self.height - 1):
                row = y * w
                next_row = (y + 1) * w
                for x in range(w - 1):
                    i = row + x
                    diffs.append(abs(frame[i] - frame[i + 1]))
                    diffs.append(abs(frame[i] - frame[next_row + x]))
            values.append(min(100.0, statistics.fmean(diffs) * 4.0 if diffs else 0.0))
        return statistics.fmean(values) if values else 0.0

    @staticmethod
    def _motion(frames: list[bytes]) -> float:
        if len(frames) < 2:
            return 0.0
        scores = []
        for a, b in zip(frames, frames[1:]):
            diff = statistics.fmean(abs(x - y) for x, y in zip(a, b))
            scores.append(min(100.0, diff * 2.5))
        return statistics.fmean(scores) if scores else 0.0

    @staticmethod
    def _exposure(frames: list[bytes]) -> float:
        scores = []
        for frame in frames:
            avg = statistics.fmean(frame)
            # Best around middle exposure; very dark/bright frames score lower.
            distance = abs(avg - 128.0) / 128.0
            scores.append(max(0.0, 100.0 * (1.0 - distance)))
        return statistics.fmean(scores) if scores else 0.0
