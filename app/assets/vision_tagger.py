from __future__ import annotations

import subprocess
from pathlib import Path

from app.models.domain import AssetShot
from app.providers.base import VisionProvider


CONTENT_TAGS = {
    "toilet", "floor_drain", "sink", "kitchen", "pipe", "machine", "worker",
    "tool", "dirty_water", "blockage", "cleaning", "success_flow", "before",
    "during", "after", "brand", "contact", "booking", "other",
}
SEMANTIC_TAGS = {
    "hook", "problem", "urgent", "professional", "proof", "result", "success",
    "trust", "conversion", "arrival", "working", "before", "after",
}

VISION_SCHEMA = {
    "type": "object",
    "properties": {
        "content_tags": {"type": "array", "items": {"type": "string"}},
        "semantic_tags": {"type": "array", "items": {"type": "string"}},
        "hook_score": {"type": "number"},
        "urgency_score": {"type": "number"},
        "proof_score": {"type": "number"},
        "result_score": {"type": "number"},
        "description": {"type": "string"},
    },
    "required": ["content_tags", "semantic_tags"],
}


class VisionAssetTagger:
    """Use a configured vision model to understand the actual frame contents."""

    def __init__(self, provider: VisionProvider) -> None:
        self.provider = provider

    def tag(self, shot: AssetShot) -> AssetShot:
        frame = self._frame_bytes(shot)
        if not frame:
            return shot
        prompt = (
            "你在分析中国本地生活管道疏通广告素材。只根据画面事实打标签，不猜测。"
            "识别马桶、地漏、洗手池、厨房、管道、师傅、机器、工具、污水、堵塞、"
            "施工过程、疏通成功/排水恢复。并给出0-100的hook/urgency/proof/result评分。"
            "禁止生成宣传承诺或价格信息。"
        )
        try:
            result = self.provider.analyze(frame, prompt, VISION_SCHEMA)
        except Exception:
            return shot

        content = set(shot.content_tags)
        semantic = set(shot.semantic_tags)
        content.update(tag for tag in result.get("content_tags", []) if tag in CONTENT_TAGS)
        semantic.update(tag for tag in result.get("semantic_tags", []) if tag in SEMANTIC_TAGS)

        return shot.model_copy(update={
            "content_tags": sorted(content),
            "semantic_tags": sorted(semantic),
            "hook_score": max(shot.hook_score, self._score(result.get("hook_score"))),
            "urgency_score": max(shot.urgency_score, self._score(result.get("urgency_score"))),
            "proof_score": max(shot.proof_score, self._score(result.get("proof_score"))),
            "result_score": max(shot.result_score, self._score(result.get("result_score"))),
        })

    def tag_many(self, shots: list[AssetShot]) -> list[AssetShot]:
        return [self.tag(shot) for shot in shots]

    @staticmethod
    def _score(value: object) -> float:
        try:
            return max(0.0, min(100.0, float(value)))
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _frame_bytes(shot: AssetShot) -> bytes:
        source = Path(shot.source_file).expanduser().resolve()
        if not source.exists():
            return b""
        middle = max(0.0, shot.start + shot.duration * 0.5)
        command = [
            "ffmpeg", "-v", "error", "-ss", f"{middle:.3f}", "-i", str(source),
            "-frames:v", "1", "-vf", "scale='min(768,iw)':-2", "-f", "image2pipe",
            "-vcodec", "mjpeg", "-",
        ]
        try:
            result = subprocess.run(command, check=True, capture_output=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            return b""
        return result.stdout
