from __future__ import annotations

import json

from app.models.domain import AdDNA, AdScript, BusinessProfile, ScriptLine
from app.providers.base import LLMProvider


class ScriptEngine:
    """Generate safe ad scripts with an optional LLM and deterministic fallback."""

    def __init__(self, llm: LLMProvider | None = None) -> None:
        self.llm = llm

    def generate(self, profile: BusinessProfile, dna: AdDNA, language: str = "普通话") -> AdScript:
        if self.llm is not None:
            try:
                return self._generate_with_llm(profile, dna, language)
            except Exception:
                # A provider outage must not stop the local planning workflow.
                pass
        return self._generate_template(profile, dna, language)

    def _generate_with_llm(self, profile: BusinessProfile, dna: AdDNA, language: str) -> AdScript:
        allowed_claims = [
            c for c in profile.approved_claims
            if c and c not in profile.forbidden_claims
        ]
        schema = {
            "type": "object",
            "required": ["lines", "title_candidates", "claims_used"],
            "properties": {
                "lines": {
                    "type": "array",
                    "minItems": 4,
                    "maxItems": 7,
                    "items": {
                        "type": "object",
                        "required": ["role", "text", "semantic_intent"],
                        "properties": {
                            "role": {"enum": ["hook", "pain", "solution", "proof", "benefit", "cta"]},
                            "text": {"type": "string"},
                            "semantic_intent": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                },
                "title_candidates": {"type": "array", "items": {"type": "string"}},
                "claims_used": {"type": "array", "items": {"type": "string"}},
            },
        }
        system_prompt = (
            "你是本地生活短视频广告脚本导演。输出严格 JSON，不要解释。"
            "脚本要口语化、短句、适合15-30秒竖屏信息流。"
            "绝对禁止创造商家未授权的承诺、价格、时效、免费、最低价、保证效果等信息。"
            "claims_used 只能从 allowed_claims 原样选择。"
        )
        user_payload = {
            "brand": profile.brand_name,
            "industry": profile.industry,
            "city": profile.city,
            "districts": profile.districts,
            "services": profile.services,
            "selected_service": dna.service,
            "strategy_id": dna.strategy_id,
            "hook_type": dna.hook_type.value,
            "pain": dna.pain,
            "fear": dna.fear,
            "proof": dna.proof,
            "cta": dna.cta,
            "target_duration": dna.target_duration,
            "language": language,
            "allowed_claims": allowed_claims,
            "forbidden_claims": profile.forbidden_claims,
        }
        raw = self.llm.generate_json(system_prompt, json.dumps(user_payload, ensure_ascii=False), schema)

        raw_claims = [str(c).strip() for c in raw.get("claims_used", []) if str(c).strip()]
        claims_used = [c for c in raw_claims if c in allowed_claims]
        lines: list[ScriptLine] = []
        for index, item in enumerate(raw.get("lines", []), start=1):
            text = str(item.get("text", "")).strip()
            role = str(item.get("role", "")).strip()
            if not text or role not in {"hook", "pain", "solution", "proof", "benefit", "cta"}:
                continue
            for forbidden in profile.forbidden_claims:
                if forbidden and forbidden in text:
                    raise ValueError(f"LLM 文案包含禁用宣传词: {forbidden}")
            lines.append(
                ScriptLine(
                    id=f"L{index}",
                    role=role,
                    text=text,
                    semantic_intent=[str(x) for x in item.get("semantic_intent", []) if str(x).strip()],
                )
            )

        if len(lines) < 4 or not any(line.role == "hook" for line in lines) or not any(line.role == "cta" for line in lines):
            raise ValueError("LLM 脚本结构不完整")

        titles = [str(x).strip() for x in raw.get("title_candidates", []) if str(x).strip()][:5]
        if not titles:
            titles = [f"{profile.city}{dna.service}｜{profile.brand_name}"]

        return AdScript(
            dna=dna,
            language=language,
            locale=profile.city,
            lines=lines,
            title_candidates=titles,
            claims_used=claims_used,
        )

    def _generate_template(self, profile: BusinessProfile, dna: AdDNA, language: str) -> AdScript:
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
            ScriptLine(id="L4", role="proof", text="现场处理后重点看排水恢复效果。", semantic_intent=["proof", "result", "success"]),
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
