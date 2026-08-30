from __future__ import annotations

from app.models.domain import AdScript, ShotRequirement


class DirectorEngine:
    """Turns script semantics into visual requirements for the asset/generation layer."""

    def plan(self, script: AdScript) -> list[ShotRequirement]:
        shots: list[ShotRequirement] = []
        for line in script.lines:
            intents = set(line.semantic_intent)
            tags: list[str] = []
            source = "real"
            emotion = None
            prompt = None

            if "problem" in intents:
                tags += [script.dna.service, "blockage", "dirty_water", "before"]
                emotion = "urgent" if "urgent" in intents else "concern"
            if "professional" in intents:
                tags += ["worker", "machine", "tool", "working"]
                prompt = f"本地家庭维修场景，专业管道疏通师傅携带设备，真实纪实风格，9:16竖屏"
                source = "either"
            if "result" in intents or "success" in intents:
                tags += [script.dna.service, "success_flow", "after", "clean_water"]
            if "cta" in intents:
                tags += ["brand", "contact", "booking"]
                source = "either"
                prompt = "本地家庭维修服务品牌收尾画面，干净可信，预留字幕和CTA区域，9:16"

            if not tags:
                tags = [script.dna.service, "working"]

            shots.append(
                ShotRequirement(
                    line_id=line.id,
                    semantic_intent=line.semantic_intent,
                    content_tags=list(dict.fromkeys(tags)),
                    emotion=emotion,
                    preferred_source=source,
                    min_duration=0.6 if line.role == "hook" else 0.8,
                    max_duration=1.6 if line.role == "hook" else 2.5,
                    generation_prompt=prompt,
                )
            )
        return shots
