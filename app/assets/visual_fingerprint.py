from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VisualFingerprint:
    value: str
    sample_time: float


class VisualFingerprintExtractor:
    """Create a lightweight perceptual-ish fingerprint from a representative frame.

    V1 intentionally avoids heavy CV dependencies. FFmpeg extracts a tiny grayscale
    frame and SHA-1 fingerprints the raw pixels. It is robust enough to catch exact
    and near-identical exported clips after normalization, while the interface can
    later be replaced by pHash/CLIP embeddings.
    """

    def extract(self, source_file: str | Path, start: float, end: float) -> VisualFingerprint | None:
        source = Path(source_file).expanduser().resolve()
        if not source.exists():
            return None
        middle = max(0.0, start + max(0.0, end - start) * 0.5)
        command = [
            "ffmpeg", "-v", "error", "-ss", f"{middle:.3f}", "-i", str(source),
            "-frames:v", "1", "-vf", "scale=32:32,format=gray", "-f", "rawvideo", "-",
        ]
        try:
            result = subprocess.run(command, check=True, capture_output=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            return None
        if not result.stdout:
            return None
        return VisualFingerprint(value=hashlib.sha1(result.stdout).hexdigest(), sample_time=middle)

    @staticmethod
    def distance(a: str | None, b: str | None) -> int:
        if not a or not b or len(a) != len(b):
            return 999
        return sum(x != y for x, y in zip(a, b))
