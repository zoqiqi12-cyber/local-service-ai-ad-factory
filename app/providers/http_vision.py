from __future__ import annotations

import base64
import json
import urllib.request

from app.providers.base import ProviderCapabilities, VisionProvider


class HTTPVisionProvider(VisionProvider):
    """Vendor-neutral synchronous vision gateway.

    Request JSON:
      {"image_base64": "...", "prompt": "...", "schema": {...}}

    Response JSON is expected to be either the structured payload directly or
    {"result": {...}}.
    """

    def __init__(self, endpoint: str, api_key: str | None = None, timeout: float = 90.0) -> None:
        self.endpoint = endpoint
        self.api_key = api_key
        self.timeout = timeout

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(supports_vision=True)

    def analyze(self, image_bytes: bytes, prompt: str, schema: dict) -> dict:
        payload = json.dumps(
            {
                "image_base64": base64.b64encode(image_bytes).decode("ascii"),
                "prompt": prompt,
                "schema": schema,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(self.endpoint, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            raw = response.read()
        parsed = json.loads(raw.decode("utf-8"))
        if isinstance(parsed, dict) and isinstance(parsed.get("result"), dict):
            return parsed["result"]
        if not isinstance(parsed, dict):
            raise RuntimeError("Vision Provider 返回格式不是 JSON object")
        return parsed
