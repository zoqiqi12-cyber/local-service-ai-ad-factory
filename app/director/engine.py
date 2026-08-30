from __future__ import annotations

from app.models.domain import AdScript, CreativeMode, ShotRequirement


class DirectorEngine:
    """Turn script semantics into paced visual requirements.

    A single spoken line may intentionally map to multiple quick shots. This is
    important for local-service ads where the viewer should see several pieces of
    visual proof during one sentence.
    """

    def plan(self, script: AdScript) -> list[ShotRequirement]:
        shots: list[ShotRequirement] = []
        for line in script.lines:
            count = self._shot_count(script, line.role)
            base = self._base_requirement(script, line)
            for index in range(count):
                tags = self._variant_tags(base.content_tags, index, line.role)
                duration_min, duration_max = self._durations(script, line.role, count)
                shots.append(
                    base.model_copy(update={
                        "content_tags": tags,
                        "min_duration": duration_min,
                        "max_duration": duration_max,
                        "generation_prompt": self._variant_prompt(base.generation_prompt, index, count),
                    })
                )
        return shots

    def _base_requirement(self, script: AdScript, line) -> ShotRequirement:
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
            prompt = "中国本地家庭维修场景，专业管道疏通师傅携带设备施工，真实纪实，不夸张，9:16竖屏"
            source = "either"
        if "result" in intents or "success" in intents:
            tags += [script.dna.service, "success_flow", "after", "clean_water"]
        if "cta" in intents:
            tags += ["brand", "contact", "booking"]
            source = "either"
            prompt = "本地家庭维修服务广告收尾，干净可信，预留品牌、字幕和CTA区域，9:16竖屏"

        if not tags:
            tags = [script.dna.service, "working"]

        return ShotRequirement(
            line_id=line.id,
            semantic_intent=line.semantic_intent,
            content_tags=list(dict.fromkeys(tags)),
            emotion=emotion,
            preferred_source=source,
            min_duration=0.5,
            max_duration=2.0,
            generation_prompt=prompt,
        )

    @staticmethod
    def _shot_count(script: AdScript, role: str) -> int:
        mode = script.dna.creative_mode
        if role == "hook":
            return 3 if mode == CreativeMode.FAST_CUT else 2
        if role in {"solution", "proof"}:
            if mode in {CreativeMode.FAST_CUT, CreativeMode.HYBRID, CreativeMode.REAL_WORK}:
                return 3
            return 2
        if role == "pain":
            return 2
        return 1

    @staticmethod
    def _durations(script: AdScript, role: str, count: int) -> tuple[float, float]:
        mode = script.dna.creative_mode
        if mode == CreativeMode.FAST_CUT:
            return (0.35, 0.85) if role != "cta" else (0.8, 1.5)
        if role == "hook":
            return (0.45, 1.0)
        if count >= 3:
            return (0.55, 1.25)
        return (0.8, 1.8)

    @staticmethod
    def _variant_tags(tags: list[str], index: int, role: str) -> list[str]:
        variants = {
            "hook": ["close_up", "overflow", "strong_motion"],
            "pain": ["before", "water_problem", "home_scene"],
            "solution": ["worker", "machine", "tool"],
            "proof": ["working", "detail", "success_flow"],
        }
        extra = variants.get(role, ["alternate_angle"])[index % len(variants.get(role, ["alternate_angle"]))]
        return list(dict.fromkeys(tags + [extra]))

    @staticmethod
    def _variant_prompt(prompt: str | None, index: int, count: int) -> str | None:
        if not prompt:
            return None
        angles = ["近景特写", "中景施工", "设备细节", "结果展示"]
        return f"{prompt}。镜头变化：{angles[index % len(angles)]}，同一人物和环境保持一致。第{index + 1}/{count}个镜头。"
