from __future__ import annotations

import json
import subprocess
from pathlib import Path
from uuid import uuid4

from app.models.domain import AssetShot

VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".mkv"}


class VideoAssetImporter:
    """Scans local video files and converts them into coarse AssetShot records.

    V1 uses the full source video as one shot. Later we can replace this with scene
    detection without changing the AssetShot contract.
    """

    def scan_folder(self, folder: str | Path) -> list[AssetShot]:
        root = Path(folder).expanduser().resolve()
        if not root.exists():
            raise FileNotFoundError(root)

        assets: list[AssetShot] = []
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
                duration = self.probe_duration(path)
                if duration <= 0:
                    continue
                assets.append(
                    AssetShot(
                        id=f"asset-{uuid4().hex[:12]}",
                        source_file=str(path),
                        start=0.0,
                        end=duration,
                        quality_score=50,
                    )
                )
        return assets

    @staticmethod
    def probe_duration(path: str | Path) -> float:
        command = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            return 0.0
        payload = json.loads(result.stdout or "{}")
        return float(payload.get("format", {}).get("duration") or 0.0)
