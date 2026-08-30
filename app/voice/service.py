from __future__ import annotations

from pathlib import Path

from app.models.domain import AdScript
from app.providers.base import TTSProvider


class VoiceService:
    """Turns a structured ad script into one narration track."""

    def __init__(self, provider: TTSProvider) -> None:
        self.provider = provider

    @staticmethod
    def narration_text(script: AdScript) -> str:
        return "。".join(line.text.strip("。！？!? ") for line in script.lines if line.text.strip()) + "。"

    def synthesize_script(self, script: AdScript, output_path: str | Path) -> Path:
        supported = set(self.provider.capabilities().languages) | set(self.provider.capabilities().dialects)
        if supported and script.language not in supported:
            raise ValueError(f"当前 TTS 不支持语言/方言：{script.language}")
        target = Path(output_path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        result = self.provider.synthesize(self.narration_text(script), script.language, str(target))
        return Path(result).expanduser().resolve()
