from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.editing.composer import FinalComposer
from app.jobs.ai_resolver import AIPendingResolver, ResolveReport
from app.jobs.pipeline import GeneratedAdPlan
from app.models.domain import BusinessProfile
from app.providers.registry import ProviderRegistry
from app.qa.validator import AdQAValidator, QAResult
from app.voice.service import VoiceService


@dataclass
class ExecutionResult:
    output_file: Path | None
    qa: QAResult
    ai: ResolveReport | None = None
    voice_file: Path | None = None


class AdExecutionEngine:
    """Executes one planned ad from timeline to final MP4.

    Expensive providers are invoked only when needed. QA runs before final render.
    """

    def __init__(self, providers: ProviderRegistry) -> None:
        self.providers = providers
        self.ai_resolver = AIPendingResolver()
        self.qa = AdQAValidator()
        self.composer = FinalComposer()

    def execute(
        self,
        profile: BusinessProfile,
        plan: GeneratedAdPlan,
        output_dir: str | Path,
        music_file: str | Path | None = None,
    ) -> ExecutionResult:
        if plan.timeline is None:
            raise ValueError("计划没有 timeline")

        root = Path(output_dir).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        timeline = plan.timeline
        ai_report: ResolveReport | None = None

        if any(c.source_type == "ai_pending" for c in timeline.clips):
            video = self.providers.require_video()
            timeline, ai_report = self.ai_resolver.resolve(
                timeline,
                video,
                root / "generated-shots",
            )

        qa = self.qa.validate(profile, plan.script, timeline)
        if not qa.ok:
            return ExecutionResult(output_file=None, qa=qa, ai=ai_report)

        voice_file: Path | None = None
        if self.providers.tts is not None:
            voice_file = VoiceService(self.providers.tts).synthesize_script(
                plan.script,
                root / "voice.mp3",
            )

        final = self.composer.compose(
            script=plan.script,
            timeline=timeline,
            output_file=root / "final.mp4",
            voice_file=voice_file,
            music_file=music_file,
            burn_subtitles=True,
        )
        return ExecutionResult(output_file=final, qa=qa, ai=ai_report, voice_file=voice_file)
