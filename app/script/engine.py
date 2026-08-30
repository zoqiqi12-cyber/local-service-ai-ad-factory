from __future__ import annotations

from app.models.domain import AdDNA, AdScript, BusinessProfile, ScriptLine


class ScriptEngine:
    """Deterministic V1 script generator. Replaceable by an LLM provider later."""

    def generate(self, profile: BusinessProfile, dna: AdDNA, language: str = "普通话") -> AdScript:
        claims = [c for c in dna.selling_points if c in profile.approved_claims and c not in profile.forbidden_claims]
        brand = profile.brand_name
        city = profile.city
        service = dna.service

        hook = self._hook(city, service, dna)
        proof = "、".join(dna.proof) if dna.proof else "专业施工"
        claim_text = "，".join(claims)
        middle = f"{brand}提供{service}服务，{proof}。"
        if claim_text:
            middle += f"{claim_text}。"

        lines = [
            ScriptLine(id="L1", role="hook", text=hook, semantic_intent=["hook", dna.hook_type.value, "problem"]),
            ScriptLine(id="L2", role="pain", text=f"遇到{dna.pain}，先别拖着不处理。", semantic_intent=["pain", "problem"]),
            ScriptLine(id="L3", role="solution", text=middle, semantic_intent=["solution", "professional", "brand"]),
            ScriptLine(id="L4", role="proof", text=f"现场处理后重点看排水恢复效果。", semantic_intent=["proof", "result", "success"]),
            ScriptLine(id="L5", role="cta", text=f"需要{service}，可通过{dna.cta}联系{brand}。", semantic_intent=["cta", "conversion"]),
        ]

        return AdScript(
            dna=dna,
            language=language,
            locale=city,
            lines=lines,
            title_candidates=[
                f"{city}{service}｜{brand}",
                f"{city}家里{service}堵了怎么办？",
                f"本地{service}服务｜{brand}",
            ],
            claims_used=claims,
        )

    @staticmethod
    def _hook(city: str, service: str, dna: AdDNA) -> str:
        hooks = {
            "local": f"在{city}，家里{service}堵了怎么办？",
            "pain": f"{service}堵塞、返水、排水慢？",
            "urgent": f"{service}突然堵了，水还在往外冒？",
            "time": f"碰上{service}堵塞，最怕需要时找不到人。",
            "price": f"找人做{service}，担心做到一半乱加价？",
            "curiosity": f"{service}反复堵，可能不只是表面问题。",
        }
        return hooks[dna.hook_type.value]
