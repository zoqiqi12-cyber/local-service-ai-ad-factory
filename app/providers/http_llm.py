from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.providers.base import LLMProvider


class HTTPJSONLLMProvider(LLMProvider):
    """Small vendor-neutral JSON LLM adapter.

    The configured endpoint receives:
      {"system_prompt": str, "user_prompt": str, "schema": object}

    It may return the generated object directly, or wrap it in ``result``.
    Secrets are read from environment variables and never stored in source.
    """

    def __init__(
        self,
        endpoint: str | None = None,
        api_key: str | None = None,
        timeout: float = 90.0,
    ) -> None:
        self.endpoint = endpoint or os.getenv("AD_FACTORY_LLM_URL", "")
        self.api_key = api_key or os.getenv("AD_FACTORY_LLM_API_KEY", "")
        self.timeout = timeout
        if not self.endpoint:
            raise ValueError("未配置 AD_FACTORY_LLM_URL")

    def generate_json(self, system_prompt: str, user_prompt: str, schema: dict) -> dict:
        payload = json.dumps(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "schema": schema,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = Request(self.endpoint, data=payload, headers=headers, method="POST")
        try:
            with urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[-2000:]
            raise RuntimeError(f"LLM HTTP {exc.code}: {body}") from exc
        except URLError as exc:
            raise RuntimeError(f"无法连接 LLM 服务: {exc.reason}") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError("LLM 服务没有返回合法 JSON") from exc

        if isinstance(data, dict) and isinstance(data.get("result"), dict):
            data = data["result"]
        if not isinstance(data, dict):
            raise RuntimeError("LLM 返回必须是 JSON object")
        return data
