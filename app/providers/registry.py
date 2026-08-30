from __future__ import annotations

from dataclasses import dataclass, field

from app.providers.base import ImageProvider, LLMProvider, TTSProvider, VideoProvider


@dataclass
class ProviderRegistry:
    """Runtime provider container; business code depends on interfaces, not vendors."""

    llm: LLMProvider | None = None
    tts: TTSProvider | None = None
    image: ImageProvider | None = None
    video: VideoProvider | None = None
    extras: dict[str, object] = field(default_factory=dict)

    def require_tts(self) -> TTSProvider:
        if self.tts is None:
            raise RuntimeError("尚未配置 TTS Provider")
        return self.tts

    def require_video(self) -> VideoProvider:
        if self.video is None:
            raise RuntimeError("尚未配置 AI Video Provider")
        return self.video

    def status(self) -> dict[str, bool]:
        return {
            "llm": self.llm is not None,
            "tts": self.tts is not None,
            "image": self.image is not None,
            "video": self.video is not None,
        }
