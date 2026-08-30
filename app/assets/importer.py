from __future__ import annotations

import json
import subprocess
from pathlib import Path
from uuid import uuid4

from app.assets.analyzer import AssetVisualAnalyzer
from app.assets.scene_splitter import FFmpegSceneSplitter
from app.assets.tagger import HeuristicAssetTagger
from app.models.domain import AssetShot

VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".mkv"}


class VideoAssetImporter:
    """Build a shot-level local asset library from raw phone footage.

    By default each source video is scene-split first, then every shot receives a
    cheap filename/folder tag pass and lightweight visual scoring/fingerprinting.
    If scene detection fails, the source video safely falls back to one full-length
    shot so import does not stop an entire batch.
    """

    def __init__(
        self,
        analyze_visuals: bool = True,
        split_scenes: bool = True,
        scene_threshold: float = 0.32,
    ) -> None:
        self.analyze_visuals = analyze_visuals
        self.split_scenes = split_scenes
        self.analyzer = AssetVisualAnalyzer()
        self.splitter = FFmpegSceneSplitter(threshold=scene_threshold)
        self.tagger = HeuristicAssetTagger()

    def scan_folder(self, folder: str | Path) -> list[AssetShot]:
        root = Path(folder).expanduser().resolve()
        if not root.exists():
            raise FileNotFoundError(root)

        assets: list[AssetShot] = []
        for path in sorted(root.rglob("*")):
            if not (path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS):
                continue
            duration = self.probe_duration(path)
            if duration <= 0:
                continue

            shots = self._split_or_fallback(path, duration)
            for shot in shots:
                shot = self.tagger.tag(shot)
                if self.analyze_visuals:
                    shot = self.analyzer.analyze(shot)
                assets.append(shot)
        return assets

    def _split_or_fallback(self, path: Path, duration: float) -> list[AssetShot]:
        if self.split_scenes:
            try:
                shots = self.splitter.split(path)
                if shots:
                    return shots
            except (FileNotFoundError, subprocess.CalledProcessError, KeyError, ValueError, json.JSONDecodeError):
                pass
        return [
            AssetShot(
                id=f"asset-{uuid4().hex[:12]}",
                source_file=str(path),
                start=0.0,
                end=duration,
                quality_score=50,
            )
        ]

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
