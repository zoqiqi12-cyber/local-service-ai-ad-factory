from __future__ import annotations

from app.assets.matcher import AssetMatcher
from app.models.domain import AdScript, AssetShot, ShotRequirement, Timeline, TimelineClip


class TimelineBuilder:
    def __init__(self) -> None:
        self.matcher = AssetMatcher()

    def build(
        self,
        script: AdScript,
        requirements: list[ShotRequirement],
        assets: list[AssetShot],
    ) -> Timeline:
        cursor = 0.0
        clips: list[TimelineClip] = []
        pool = [asset.model_copy(deep=True) for asset in assets]
        selected_assets: list[AssetShot] = []

        for req in requirements:
            asset = self.matcher.best(req, pool, selected=selected_assets)
            target = min(max(req.min_duration, 1.2), req.max_duration)

            if asset is not None and req.preferred_source != "ai":
                duration = min(target, asset.duration)
                clips.append(
                    TimelineClip(
                        line_id=req.line_id,
                        asset_id=asset.id,
                        source_file=asset.source_file,
                        source_start=asset.start,
                        source_end=asset.start + duration,
                        timeline_start=cursor,
                        timeline_end=cursor + duration,
                        source_type="real",
                    )
                )
                cursor += duration
                selected_assets.append(asset.model_copy(deep=True))
                for candidate in pool:
                    if candidate.id == asset.id:
                        candidate.used_count += 1
                        break
            else:
                clips.append(
                    TimelineClip(
                        line_id=req.line_id,
                        timeline_start=cursor,
                        timeline_end=cursor + target,
                        source_type="ai_pending",
                        generation_prompt=req.generation_prompt or self._default_prompt(script, req),
                    )
                )
                cursor += target

        return Timeline(
            duration=cursor,
            clips=clips,
            voice_language=script.language,
            title=script.title_candidates[0] if script.title_candidates else script.dna.service,
        )

    @staticmethod
    def _default_prompt(script: AdScript, req: ShotRequirement) -> str:
        tags = "、".join(req.content_tags)
        return f"中国本地家庭维修广告场景，主题：{tags}，真实纪实，避免夸张，9:16竖屏"
