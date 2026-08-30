from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderCapabilities:
    languages: tuple[str, ...] = ()
    dialects: tuple[str, ...] = ()
    max_video_seconds: float | None = None
    supports_image_to_video: bool = False
    supports_text_to_video: bool = False


class LLMProvider(ABC):
    @abstractmethod
    def generate_json(self, system_prompt: str, user_prompt: str, schema: dict) -> dict:
        raise NotImplementedError


class TTSProvider(ABC):
    @abstractmethod
    def capabilities(self) -> ProviderCapabilities:
        raise NotImplementedError

    @abstractmethod
    def synthesize(self, text: str, language: str, output_path: str) -> str:
        raise NotImplementedError


class VideoProvider(ABC):
    @abstractmethod
    def capabilities(self) -> ProviderCapabilities:
        raise NotImplementedError

    @abstractmethod
    def generate(self, prompt: str, duration: float, output_path: str) -> str:
        raise NotImplementedError


class ImageProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, output_path: str) -> str:
        raise NotImplementedError
