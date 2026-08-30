from __future__ import annotations

import random

from app.campaign.history import dna_fingerprint
from app.models.domain import AdDNA, BusinessProfile, CreativeMode, HookType


STRATEGIES = {
    "A01": (HookType.LOCAL, "多业务关键词覆盖"),
    "A02": (HookType.LOCAL, "附近快速上门"),
    "A03": (HookType.LOCAL, "本地口播"),
    "A04": (HookType.URGENT, "紧急需求"),
    "A05": (HookType.LOCAL, "搜索承接"),
    "A06": (HookType.TIME, "服务覆盖时间"),
    "A07": (HookType.PAIN, "痛点品牌利益"),
    "A08": (HookType.PRICE, "价格信任"),
    "A09": (HookType.PAIN, "专业证明"),
    "A10": (HookType.CURIOSITY, "品牌人物"),
}

CREATIVE_MODES = [
    CreativeMode.HYBRID,
    CreativeMode.FAST_CUT,
    CreativeMode.REAL_WORK,
    CreativeMode.SPOKESPERSON,
    CreativeMode.AI_SCENE,
]

FEARS = [
    None,
    "担心维修不透明",
    "担心上门太慢",
    "担心处理后又堵",
    "担心师傅不专业",
]


class CampaignBrain:
    """Build diverse structured ad ideas before any prose is written."""

    def build_matrix(
        self,
        profile: BusinessProfile,
        count: int,
        duration: int = 20,
        seen_fingerprints: set[str] | None = None,
    ) -> list[AdDNA]:
        if not profile.services:
            raise ValueError("BusinessProfile.services cannot be empty")

        seen = seen_fingerprints or set()
        candidates: list[AdDNA] = []
        strategy_ids = list(STRATEGIES)
        allowed_claims = [c for c in profile.approved_claims if c not in profile.forbidden_claims]
        ctas = profile.booking_methods or ["立即咨询"]

        # Produce a pool much larger than the requested batch, then select the least-repeated ideas.
        pool_size = max(count * 6, 40)
        for index in range(pool_size):
            strategy_id = strategy_ids[index % len(strategy_ids)]
            hook_type, _ = STRATEGIES[strategy_id]
            service = profile.services[(index // len(strategy_ids) + index) % len(profile.services)]
            mode = CREATIVE_MODES[(index + strategy_ids.index(strategy_id)) % len(CREATIVE_MODES)]
            fear = FEARS[(index // 2) % len(FEARS)]
            if strategy_id == "A08":
                fear = "担心维修不透明"

            selling_points = self._rotating_claims(allowed_claims, index, limit=2)
            proof_options = [
                ["真实施工", "疏通结果"],
                ["专业设备", "现场操作"],
                ["堵塞前后对比", "排水恢复"],
                ["真人师傅", "施工过程"],
            ]
            candidates.append(
                AdDNA(
                    strategy_id=strategy_id,
                    hook_type=hook_type,
                    pain=f"{service}堵塞或排水异常",
                    fear=fear,
                    service=service,
                    selling_points=selling_points,
                    proof=proof_options[index % len(proof_options)],
                    trust=selling_points,
                    cta=ctas[index % len(ctas)],
                    creative_mode=mode,
                    target_duration=duration,
                )
            )

        unseen = [dna for dna in candidates if dna_fingerprint(dna) not in seen]
        fallback = [dna for dna in candidates if dna_fingerprint(dna) in seen]
        random.shuffle(unseen)
        random.shuffle(fallback)
        selected = (unseen + fallback)[:count]
        return selected

    @staticmethod
    def _rotating_claims(allowed: list[str], offset: int, limit: int) -> list[str]:
        if not allowed:
            return []
        return [allowed[(offset + step) % len(allowed)] for step in range(min(limit, len(allowed)))]
