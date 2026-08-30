from __future__ import annotations

from dataclasses import dataclass

from app.campaign.brain import CampaignBrain
from app.campaign.history import CampaignHistory
from app.director.engine import DirectorEngine
from app.editing.timeline import TimelineBuilder
from app.localizer.engine import Localizer
from app.models.domain import AdScript, AssetShot, BusinessProfile, ShotRequirement, Timeline
from app.providers.registry import ProviderRegistry
from app.script.engine import ScriptEngine


@dataclass
class GeneratedAdPlan:
    script: AdScript
    shots: list[ShotRequirement]
    timeline: Timeline | None = None

    def model_dump(self) -> dict:
        return {
            "script": self.script.model_dump(mode="json"),
            "shots": [shot.model_dump(mode="json") for shot in self.shots],
            "timeline": self.timeline.model_dump(mode="json") if self.timeline else None,
        }


class AdFactoryPipeline:
    """Planning pipeline. Works offline, but uses configured providers when present."""

    def __init__(
        self,
        providers: ProviderRegistry | None = None,
        history: CampaignHistory | None = None,
    ) -> None:
        self.providers = providers or ProviderRegistry()
        self.history = history
        self.campaign = CampaignBrain()
        self.scripts = ScriptEngine(llm=self.providers.llm)
        self.localizer = Localizer()
        self.director = DirectorEngine()
        self.timeline = TimelineBuilder()

    def generate_plans(
        self,
        profile: BusinessProfile,
        count: int,
        duration: int = 20,
        language: str = "普通话",
        assets: list[AssetShot] | None = None,
    ) -> list[GeneratedAdPlan]:
        seen = self.history.seen_dna() if self.history else set()
        dnas = self.campaign.build_matrix(
            profile,
            count=count,
            duration=duration,
            seen_fingerprints=seen,
        )
        plans: list[GeneratedAdPlan] = []
        for dna in dnas:
            script = self.scripts.generate(profile, dna, language="普通话")
            script = self.localizer.localize(script, target=language)
            shots = self.director.plan(script)
            timeline = self.timeline.build(script, shots, assets or [])
            plans.append(GeneratedAdPlan(script=script, shots=shots, timeline=timeline))
        return plans
