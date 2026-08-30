from __future__ import annotations

import json
import shutil
import sys

from app.providers.registry import ProviderRegistry


def check() -> dict:
    providers = ProviderRegistry.from_env()
    return {
        "python": sys.version.split()[0],
        "ffmpeg": shutil.which("ffmpeg") is not None,
        "ffprobe": shutil.which("ffprobe") is not None,
        "providers": providers.status(),
        "ready_for_offline_planning": True,
        "ready_for_real_video_only_render": shutil.which("ffmpeg") is not None,
        "ready_for_full_ai_generation": (
            shutil.which("ffmpeg") is not None
            and providers.video is not None
        ),
    }


def main() -> None:
    payload = check()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if not payload["ffmpeg"] or not payload["ffprobe"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
