from __future__ import annotations

import random
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


class CampaignBrain:
    """Builds diverse structured ad ideas before any prose is written."""

    def build_matrix(self, profile: BusinessProfile, count: int, duration: int = 20) -> list[AdDNA]:
        if not profile.services:
            raise ValueError("BusinessProfile.services cannot be empty")

        strategy_ids = list(STRATEGIES)
        result: list[AdDNA] = []
        for index in range(count):
            strategy_id = strategy_ids[index % len(strategy_ids)]
            hook_type, _ = STRATEGIES[strategy_id]
            service = profile.services[index % len(profile.services)]
            selling_points = self._safe_claim_sample(profile, 2)
            result.append(
                AdDNA(
                    strategy_id=strategy_id,
                    hook_type=hook_type,
                    pain=f"{service}堵塞或排水异常",
                    fear="担心维修不透明" if strategy_id == "A08" else None,
                    service=service,
                    selling_points=selling_points,
                    proof=["真实施工", "疏通结果"],
                    trust=selling_points,
                    cta=profile.booking_methods[0] if profile.booking_methods else "立即咨询",
                    creative_mode=CreativeMode.HYBRID,
                    target_duration=duration,
                )
            )
        random.shuffle(result)
        return result

    @staticmethod
    def _safe_claim_sample(profile: BusinessProfile, limit: int) -> list[str]:
        allowed = [c for c in profile.approved_claims if c not in profile.forbidden_claims]
        return allowed[:limit]
