from __future__ import annotations

import re
from pathlib import Path

from app.models.domain import AssetShot


TAG_RULES: dict[str, tuple[str, ...]] = {
    "toilet": ("马桶", "坐便", "toilet"),
    "floor_drain": ("地漏", "floor-drain", "floor_drain"),
    "sink": ("洗手池", "洗脸盆", "台盆", "sink"),
    "kitchen": ("厨房", "水槽", "kitchen"),
    "pipe": ("管道", "主管", "下水道", "pipe", "drain"),
    "machine": ("机器", "设备", "疏通机", "machine"),
    "worker": ("师傅", "维修", "上门", "worker"),
    "dirty_water": ("污水", "脏水", "返水", "dirty"),
    "blockage": ("堵", "堵塞", "不下水", "block"),
    "success_flow": ("通了", "畅通", "排水", "效果", "after", "success"),
}


class HeuristicAssetTagger:
    """Cheap, explainable first-pass tagger.

    It intentionally does not pretend to understand video pixels. It uses file and
    folder names plus existing shot metadata so users can get value before a vision
    provider is configured. A later vision tagger can merge/override these tags.
    """

    def tag(self, shot: AssetShot) -> AssetShot:
        text = str(Path(shot.source_file)).lower()
        content = set(shot.content_tags)
        semantic = set(shot.semantic_tags)

        for tag, needles in TAG_RULES.items():
            if any(needle.lower() in text for needle in needles):
                content.add(tag)

        if {"blockage", "dirty_water"} & content:
            semantic.update({"problem", "urgent"})
        if {"machine", "worker"} & content:
            semantic.update({"professional", "proof"})
        if "success_flow" in content:
            semantic.update({"result", "success", "after"})

        # A modest baseline only; vision analysis can later replace these scores.
        hook = shot.hook_score
        urgency = shot.urgency_score
        proof = shot.proof_score
        result = shot.result_score
        quality = shot.quality_score or 50.0

        if "problem" in semantic:
            hook = max(hook, 62.0)
        if "urgent" in semantic:
            urgency = max(urgency, 68.0)
        if "proof" in semantic:
            proof = max(proof, 65.0)
        if "result" in semantic:
            result = max(result, 75.0)

        # Penalize obvious duplicate/export naming artifacts slightly.
        if re.search(r"(?:copy|副本|重复|\(\d+\))", text):
            quality = max(0.0, quality - 8.0)

        return shot.model_copy(update={
            "content_tags": sorted(content),
            "semantic_tags": sorted(semantic),
            "quality_score": quality,
            "hook_score": hook,
            "urgency_score": urgency,
            "proof_score": proof,
            "result_score": result,
        })

    def tag_many(self, shots: list[AssetShot]) -> list[AssetShot]:
        return [self.tag(shot) for shot in shots]
