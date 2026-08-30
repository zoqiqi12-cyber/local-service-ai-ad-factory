from __future__ import annotations

from app.assets.visual_fingerprint import VisualFingerprintExtractor
from app.models.domain import AssetShot, ShotRequirement


class AssetMatcher:
    """Scores real shots against semantic and visual requirements.

    Selection is explainable: semantic overlap remains the strongest signal, while
    quality, motion and visual-diversity penalties change depending on the ad phase.
    """

    def rank(
        self,
        requirement: ShotRequirement,
        assets: list[AssetShot],
        selected: list[AssetShot] | None = None,
    ) -> list[AssetShot]:
        selected = selected or []
        return sorted(
            assets,
            key=lambda asset: self.score(requirement, asset, selected),
            reverse=True,
        )

    def best(
        self,
        requirement: ShotRequirement,
        assets: list[AssetShot],
        selected: list[AssetShot] | None = None,
    ) -> AssetShot | None:
        ranked = self.rank(requirement, assets, selected=selected)
        if not ranked:
            return None
        best = ranked[0]
        return best if self.score(requirement, best, selected or []) > 0 else None

    @staticmethod
    def score(
        requirement: ShotRequirement,
        asset: AssetShot,
        selected: list[AssetShot] | None = None,
    ) -> float:
        selected = selected or []
        wanted = set(requirement.content_tags) | set(requirement.semantic_intent)
        actual = set(asset.content_tags) | set(asset.semantic_tags)
        overlap = len(wanted & actual)
        score = overlap * 20.0 + asset.quality_score * 0.14 + asset.sharpness_score * 0.06

        intents = set(requirement.semantic_intent)
        if "hook" in intents:
            score += asset.hook_score * 0.32
            score += asset.motion_score * 0.20
            score += asset.urgency_score * 0.12
        if "urgent" in intents or requirement.emotion == "urgent":
            score += asset.urgency_score * 0.28
            score += asset.motion_score * 0.12
        if "proof" in intents or "professional" in intents:
            score += asset.proof_score * 0.28
            score += asset.stability_score * 0.10
            score += asset.sharpness_score * 0.08
        if "result" in intents or "success" in intents:
            score += asset.result_score * 0.38
            score += asset.stability_score * 0.18
            score += asset.sharpness_score * 0.10

        score -= asset.used_count * 10.0
        if asset.duration < requirement.min_duration:
            score -= 35.0

        # Prefer changing source clips instead of repeatedly cropping one original.
        same_source_count = sum(1 for item in selected if item.source_file == asset.source_file)
        score -= same_source_count * 16.0

        # Strongly suppress shots that look nearly identical to anything already used
        # in the same ad, even when they have different filenames/ids.
        for previous in selected:
            similarity = VisualFingerprintExtractor.similarity(
                asset.visual_fingerprint,
                previous.visual_fingerprint,
            )
            if similarity >= 0.96:
                score -= 70.0
            elif similarity >= 0.90:
                score -= 38.0
            elif similarity >= 0.84:
                score -= 16.0
        return score
