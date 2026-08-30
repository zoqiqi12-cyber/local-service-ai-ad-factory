from __future__ import annotations

import os
from dataclasses import dataclass, field

from app.providers.base import ImageProvider, LLMProvider, TTSProvider, VideoProvider, VisionProvider
from app.settings import ProviderSettings, SettingsStore


@dataclass
class ProviderRegistry:
    """Runtime provider container; business code depends on interfaces, not vendors."""

    llm: LLMProvider | None = None
    tts: TTSProvider | None = None
    image: ImageProvider | None = None
    video: VideoProvider | None = None
    vision: VisionProvider | None = None
    extras: dict[str, object] = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> "ProviderRegistry":
        return cls._from_values(None)

    @classmethod
    def from_local_settings(cls, store: SettingsStore | None = None) -> "ProviderRegistry":
        settings = (store or SettingsStore()).load()
        return cls._from_values(settings)

    @classmethod
    def _from_values(cls, settings: ProviderSettings | None) -> "ProviderRegistry":
        from app.providers.http_adapters import HTTPTTSProvider, HTTPVideoProvider
        from app.providers.http_llm import HTTPJSONLLMProvider
        from app.providers.http_vision import HTTPVisionProvider

        def value(env_name: str, local_value: str = "") -> str | None:
            raw = os.getenv(env_name)
            if raw and raw.strip():
                return raw.strip()
            return local_value.strip() or None

        settings = settings or ProviderSettings()
        registry = cls()

        llm_endpoint = value("AD_FACTORY_LLM_URL", settings.llm_url)
        llm_key = value("AD_FACTORY_LLM_API_KEY", settings.llm_api_key)
        vision_endpoint = value("AD_FACTORY_VISION_ENDPOINT", settings.vision_url)
        vision_key = value("AD_FACTORY_VISION_API_KEY", settings.vision_api_key)
        tts_endpoint = value("AD_FACTORY_TTS_ENDPOINT", settings.tts_url)
        tts_key = value("AD_FACTORY_TTS_API_KEY", settings.tts_api_key)
        video_endpoint = value("AD_FACTORY_VIDEO_ENDPOINT", settings.video_url)
        video_key = value("AD_FACTORY_VIDEO_API_KEY", settings.video_api_key)

        if llm_endpoint:
            registry.llm = HTTPJSONLLMProvider(endpoint=llm_endpoint, api_key=llm_key)

        if vision_endpoint:
            registry.vision = HTTPVisionProvider(endpoint=vision_endpoint, api_key=vision_key)

        if tts_endpoint:
            languages_text = value("AD_FACTORY_TTS_LANGUAGES", settings.tts_languages) or "普通话"
            dialects_text = value("AD_FACTORY_TTS_DIALECTS", settings.tts_dialects) or ""
            languages = tuple(item.strip() for item in languages_text.split(",") if item.strip())
            dialects = tuple(item.strip() for item in dialects_text.split(",") if item.strip())
            registry.tts = HTTPTTSProvider(
                endpoint=tts_endpoint,
                api_key=tts_key,
                languages=languages,
                dialects=dialects,
            )

        if video_endpoint:
            max_seconds_text = value("AD_FACTORY_VIDEO_MAX_SECONDS", settings.video_max_seconds)
            registry.video = HTTPVideoProvider(
                endpoint=video_endpoint,
                api_key=video_key,
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

    def require_vision(self) -> VisionProvider:
        if self.vision is None:
            raise RuntimeError("尚未配置 Vision Provider")
        return self.vision

    def status(self) -> dict[str, bool]:
        return {
            "llm": self.llm is not None,
            "tts": self.tts is not None,
            "image": self.image is not None,
            "video": self.video is not None,
            "vision": self.vision is not None,
        }
