from __future__ import annotations

from copy import deepcopy
from app.models.domain import AdScript


class Localizer:
    """V1 local language rewriter with safe fallbacks.

    This is intentionally conservative. Real dialect generation should be delegated
    to a capable LLM/TTS provider that explicitly declares support.
    """

    def localize(self, script: AdScript, target: str) -> AdScript:
        localized = deepcopy(script)
        localized.language = target

        if target in {"普通话", "standard_zh"}:
            return localized

        if target in {"广东口语", "中山口语"}:
            replacements = {
                "家里": "屋企",
                "怎么办": "点处理好",
                "先别拖着不处理": "唔好一直拖住",
                "需要": "有需要",
            }
            for line in localized.lines:
                for src, dst in replacements.items():
                    line.text = line.text.replace(src, dst)
            return localized

        # Unknown dialect: preserve Mandarin text instead of pretending support.
        localized.language = f"{target}（回退普通话文本）"
        return localized
