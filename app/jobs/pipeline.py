from __future__ import annotations

from dataclasses import dataclass
from app.campaign.brain import CampaignBrain
from app.director.engine import DirectorEngine
from app.localizer.engine import Localizer
from app.models.domain import AdScript, BusinessProfile, ShotRequirement
from app.script.engine import ScriptEngine


@dataclass
class GeneratedAdPlan:
    script: AdScript
    shots: list[ShotRequirement]

    def model_dump(self) -> dict:
        return {
            "script": self.script.model_dump(mode="json"),
            "shots": [shot.model_dump(mode="json") for shot in self.shots],
        }


class AdFactoryPipeline:
    """Runnable V1 planning pipeline with no external AI dependency."""

    def __init__(self) -> None:
        self.campaign = CampaignBrain()
        self.scripts = ScriptEngine()
        self.localizer = Localizer()
        self.director = DirectorEngine()

    def generate_plans(
        self,
        profile: BusinessProfile,
        count: int,
        duration: int = 20,
        language: str = "普通话",
    ) -> list[GeneratedAdPlan]:
        dnas = self.campaign.build_matrix(profile, count=count, duration=duration)
        plans: list[GeneratedAdPlan] = []
        for dna in dnas:
            script = self.scripts.generate(profile, dna, language="普通话")
            script = self.localizer.localize(script, target=language)
            shots = self.director.plan(script)
            plans.append(GeneratedAdPlan(script=script, shots=shots))
        return plans
