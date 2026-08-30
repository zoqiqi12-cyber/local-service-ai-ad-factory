from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class ProviderSettings:
    llm_url: str = ""
    llm_api_key: str = ""
    vision_url: str = ""
    vision_api_key: str = ""
    tts_url: str = ""
    tts_api_key: str = ""
    tts_languages: str = "普通话"
    tts_dialects: str = "粤语,中山口语"
    video_url: str = ""
    video_api_key: str = ""
    video_max_seconds: str = "10"


class SettingsStore:
    """Stores user-owned provider config outside the source tree.

    This is intentionally a local desktop convenience layer. Environment variables
    still override these values in ProviderRegistry, which is useful for servers/CI.
    API keys never need to be committed to GitHub.
    """

    def __init__(self, path: str | Path | None = None) -> None:
        default = Path.home() / ".local_service_ai_ad_factory" / "settings.json"
        self.path = Path(path).expanduser().resolve() if path else default

    def load(self) -> ProviderSettings:
        if not self.path.exists():
            return ProviderSettings()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return ProviderSettings()
        allowed = ProviderSettings.__dataclass_fields__.keys()
        return ProviderSettings(**{k: str(v or "") for k, v in data.items() if k in allowed})

    def save(self, settings: ProviderSettings) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(asdict(settings), ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass
        return self.path
