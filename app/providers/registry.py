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

    @classmethod
    def from_env(cls) -> "ProviderRegistry":
        """Create optional vendor-neutral HTTP providers from environment variables."""
        from app.providers.http_adapters import HTTPTTSProvider, HTTPVideoProvider, provider_env
        from app.providers.http_llm import HTTPJSONLLMProvider

        registry = cls()
        llm_endpoint = provider_env("AD_FACTORY_LLM_URL")
        tts_endpoint = provider_env("AD_FACTORY_TTS_ENDPOINT")
        video_endpoint = provider_env("AD_FACTORY_VIDEO_ENDPOINT")

        if llm_endpoint:
            registry.llm = HTTPJSONLLMProvider(
                endpoint=llm_endpoint,
                api_key=provider_env("AD_FACTORY_LLM_API_KEY"),
            )

        if tts_endpoint:
            languages = tuple(
                item.strip()
                for item in (provider_env("AD_FACTORY_TTS_LANGUAGES") or "普通话").split(",")
                if item.strip()
            )
            dialects = tuple(
                item.strip()
                for item in (provider_env("AD_FACTORY_TTS_DIALECTS") or "").split(",")
                if item.strip()
            )
            registry.tts = HTTPTTSProvider(
                endpoint=tts_endpoint,
                api_key=provider_env("AD_FACTORY_TTS_API_KEY"),
                languages=languages,
                dialects=dialects,
            )

        if video_endpoint:
            max_seconds_text = provider_env("AD_FACTORY_VIDEO_MAX_SECONDS")
            registry.video = HTTPVideoProvider(
                endpoint=video_endpoint,
                api_key=provider_env("AD_FACTORY_VIDEO_API_KEY"),
                max_video_seconds=float(max_seconds_text) if max_seconds_text else None,
            )
        return registry

    def require_llm(self) -> LLMProvider:
        if self.llm is None:
            raise RuntimeError("尚未配置 LLM Provider")
        return self.llm

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
