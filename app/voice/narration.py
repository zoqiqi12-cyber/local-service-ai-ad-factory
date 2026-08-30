from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.models.domain import AdScript


class TTSProvider(Protocol):
    def synthesize(self, text: str, language: str, output_path: str) -> str:
        """Return local audio path after synthesis."""
        ...


@dataclass
class NarrationResult:
    audio_path: str
    text: str
    language: str


class NarrationEngine:
    """Turns the final localized script into one narration track."""

    def script_text(self, script: AdScript) -> str:
        return "。".join(line.text.strip("。！？!? ") for line in script.lines if line.text.strip()) + "。"

    def generate(
        self,
        script: AdScript,
        provider: TTSProvider,
        output_path: str | Path,
    ) -> NarrationResult:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        text = self.script_text(script)
        result = provider.synthesize(text=text, language=script.language, output_path=str(path))
        return NarrationResult(audio_path=result, text=text, language=script.language)
