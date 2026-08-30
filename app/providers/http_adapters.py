from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

from app.providers.base import ProviderCapabilities, TTSProvider, VideoProvider


class _HTTPMixin:
    def __init__(self, endpoint: str, api_key: str | None = None, timeout: int = 300) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _post(self, payload: dict) -> tuple[bytes, str]:
        headers = {"Content-Type": "application/json", "Accept": "application/json, audio/*, video/*"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = Request(
            self.endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urlopen(request, timeout=self.timeout) as response:
            return response.read(), response.headers.get("Content-Type", "")

    @staticmethod
    def _download(url: str, output_path: str, timeout: int) -> str:
        target = Path(output_path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        request = Request(url, headers={"User-Agent": "local-service-ai-ad-factory/0.1"})
        with urlopen(request, timeout=timeout) as response:
            target.write_bytes(response.read())
        return str(target)


class HTTPVideoProvider(_HTTPMixin, VideoProvider):
    """Simple synchronous HTTP video adapter.

    Endpoint contract:
      request JSON: {prompt, duration, aspect_ratio, output_format}
      response: video bytes OR JSON containing file_url / video_url / url.

    Async vendor APIs should be wrapped by a small gateway that exposes this
    stable contract, keeping the app independent from any single AI vendor.
    """

    def __init__(
        self,
        endpoint: str,
        api_key: str | None = None,
        timeout: int = 600,
        max_video_seconds: float | None = None,
    ) -> None:
        super().__init__(endpoint, api_key, timeout)
        self._max_video_seconds = max_video_seconds

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            max_video_seconds=self._max_video_seconds,
            supports_text_to_video=True,
        )

    def generate(self, prompt: str, duration: float, output_path: str) -> str:
        if self._max_video_seconds and duration > self._max_video_seconds:
            raise ValueError(f"AI 视频 Provider 单镜头最长 {self._max_video_seconds}s")
        body, content_type = self._post({
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": "9:16",
            "output_format": "mp4",
        })
        target = Path(output_path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        if content_type.startswith("video/") or content_type == "application/octet-stream":
            target.write_bytes(body)
            return str(target)
        data = json.loads(body.decode("utf-8"))
        url = data.get("file_url") or data.get("video_url") or data.get("url")
        if not url:
            raise RuntimeError("AI Video HTTP 返回中没有 file_url/video_url/url")
        return self._download(url, str(target), self.timeout)


class HTTPTTSProvider(_HTTPMixin, TTSProvider):
    """Simple synchronous TTS adapter.

    Endpoint contract:
      request JSON: {text, language, output_format}
      response: audio bytes OR JSON containing file_url / audio_url / url.
    """

    def __init__(
        self,
        endpoint: str,
        api_key: str | None = None,
        timeout: int = 180,
        languages: tuple[str, ...] = ("普通话",),
        dialects: tuple[str, ...] = (),
    ) -> None:
        super().__init__(endpoint, api_key, timeout)
        self._languages = languages
        self._dialects = dialects

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(languages=self._languages, dialects=self._dialects)

    def synthesize(self, text: str, language: str, output_path: str) -> str:
        body, content_type = self._post({
            "text": text,
            "language": language,
            "output_format": "wav",
        })
        target = Path(output_path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        if content_type.startswith("audio/") or content_type == "application/octet-stream":
            target.write_bytes(body)
            return str(target)
        data = json.loads(body.decode("utf-8"))
        url = data.get("file_url") or data.get("audio_url") or data.get("url")
        if not url:
            raise RuntimeError("TTS HTTP 返回中没有 file_url/audio_url/url")
        return self._download(url, str(target), self.timeout)


def provider_env(name: str) -> str | None:
    value = os.getenv(name)
    return value.strip() if value and value.strip() else None
