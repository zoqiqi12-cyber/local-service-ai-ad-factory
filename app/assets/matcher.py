from __future__ import annotations

from app.models.domain import AssetShot, ShotRequirement


class AssetMatcher:
    """Scores real shots against semantic requirements.

    V1 is deterministic and explainable. Later versions can blend embeddings and
    vision-model scores without changing the caller contract.
    """

    def rank(self, requirement: ShotRequirement, assets: list[AssetShot]) -> list[AssetShot]:
        return sorted(assets, key=lambda asset: self.score(requirement, asset), reverse=True)

    def best(self, requirement: ShotRequirement, assets: list[AssetShot]) -> AssetShot | None:
        ranked = self.rank(requirement, assets)
        if not ranked:
            return None
        best = ranked[0]
        return best if self.score(requirement, best) > 0 else None

    @staticmethod
    def score(requirement: ShotRequirement, asset: AssetShot) -> float:
        wanted = set(requirement.content_tags) | set(requirement.semantic_intent)
        actual = set(asset.content_tags) | set(asset.semantic_tags)
        overlap = len(wanted & actual)
        score = overlap * 20.0 + asset.quality_score * 0.15

        if "hook" in requirement.semantic_intent:
            score += asset.hook_score * 0.35
        if "urgent" in requirement.semantic_intent or requirement.emotion == "urgent":
            score += asset.urgency_score * 0.30
        if "proof" in requirement.semantic_intent:
            score += asset.proof_score * 0.30
        if "result" in requirement.semantic_intent or "success" in requirement.semantic_intent:
            score += asset.result_score * 0.40

        score -= asset.used_count * 8.0
        if asset.duration < requirement.min_duration:
            score -= 30.0
        return score
