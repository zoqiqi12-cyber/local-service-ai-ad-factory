from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VisualFingerprint:
    value: str
    sample_time: float


class VisualFingerprintExtractor:
    """Create a lightweight perceptual fingerprint from a representative frame.

    FFmpeg extracts a normalized 16x16 grayscale frame. We turn the pixels into an
    average-hash bit string, encoded as 64 hex characters. Unlike hashing raw bytes,
    this survives small re-encodes, brightness changes and mild resize/crop noise.
    """

    SIZE = 16

    def extract(self, source_file: str | Path, start: float, end: float) -> VisualFingerprint | None:
        source = Path(source_file).expanduser().resolve()
        if not source.exists():
            return None
        middle = max(0.0, start + max(0.0, end - start) * 0.5)
        command = [
            "ffmpeg", "-v", "error", "-ss", f"{middle:.3f}", "-i", str(source),
            "-frames:v", "1",
            "-vf", f"scale={self.SIZE}:{self.SIZE}:force_original_aspect_ratio=increase,crop={self.SIZE}:{self.SIZE},format=gray",
            "-f", "rawvideo", "-",
        ]
        try:
            result = subprocess.run(command, check=True, capture_output=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            return None
        pixels = result.stdout
        if len(pixels) < self.SIZE * self.SIZE:
            return None
        pixels = pixels[: self.SIZE * self.SIZE]
        mean = sum(pixels) / len(pixels)
        bits = "".join("1" if value >= mean else "0" for value in pixels)
        value = f"{int(bits, 2):0{len(bits) // 4}x}"
        return VisualFingerprint(value=value, sample_time=middle)

    @staticmethod
    def distance(a: str | None, b: str | None) -> int:
        """Bit-level Hamming distance. Lower means more visually similar."""
        if not a or not b or len(a) != len(b):
            return 999
        try:
            return (int(a, 16) ^ int(b, 16)).bit_count()
        except ValueError:
            return 999

    @staticmethod
    def similarity(a: str | None, b: str | None) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        total_bits = len(a) * 4
        distance = VisualFingerprintExtractor.distance(a, b)
        if distance > total_bits:
            return 0.0
        return max(0.0, 1.0 - distance / total_bits)
