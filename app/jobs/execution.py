from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.editing.composer import FinalComposer
from app.jobs.ai_resolver import AIPendingResolver, ResolveReport
from app.jobs.pipeline import GeneratedAdPlan
from app.models.domain import BusinessProfile, Timeline
from app.providers.registry import ProviderRegistry
from app.qa.validator import AdQAValidator, QAResult
from app.voice.service import VoiceService


@dataclass
class ExecutionResult:
    output_file: str | None
    timeline: Timeline
    qa: QAResult
    ai_report: ResolveReport | None = None
    voice_file: str | None = None
    warnings: list[str] = field(default_factory=list)


class AdExecutionEngine:
    """Execute one generated plan all the way to a final MP4.

    The engine is provider-agnostic. If the timeline contains AI-pending shots,
    a VideoProvider must be configured. TTS is optional: without it the result
    can still be rendered with subtitles only.
    """

    def __init__(self, providers: ProviderRegistry | None = None) -> None:
        self.providers = providers or ProviderRegistry()
        self.ai_resolver = AIPendingResolver()
        self.qa = AdQAValidator()
        self.composer = FinalComposer()

    def execute(
        self,
        profile: BusinessProfile,
        plan: GeneratedAdPlan,
        output_dir: str | Path,
        music_file: str | Path | None = None,
        require_voice: bool = False,
    ) -> ExecutionResult:
        if plan.timeline is None:
            raise ValueError("广告方案尚未生成 timeline")

        root = Path(output_dir).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        timeline = plan.timeline.model_copy(deep=True)
        warnings: list[str] = []
        ai_report: ResolveReport | None = None

        if any(c.source_type == "ai_pending" for c in timeline.clips):
            if self.providers.video is None:
                preflight = self.qa.validate(profile, plan.script, timeline)
                return ExecutionResult(
                    output_file=None,
                    timeline=timeline,
                    qa=preflight,
                    warnings=["缺少 AI Video Provider，无法补齐缺失镜头"],
                )
            timeline, ai_report = self.ai_resolver.resolve(
                timeline,
                self.providers.require_video(),
                root / "generated_shots",
            )

        voice_file: str | None = None
        if self.providers.tts is not None:
            voice_path = VoiceService(self.providers.require_tts()).synthesize_script(
                plan.script,
                root / "voice.wav",
            )
            voice_file = str(voice_path)
        elif require_voice:
            check = self.qa.validate(profile, plan.script, timeline)
            check.errors.append("未配置 TTS Provider")
            check.ok = False
            return ExecutionResult(
                output_file=None,
                timeline=timeline,
                qa=check,
                ai_report=ai_report,
                warnings=warnings,
            )
        else:
            warnings.append("未配置 TTS，当前将输出仅字幕版本")

        qa = self.qa.validate(profile, plan.script, timeline)
        if not qa.ok:
            return ExecutionResult(
                output_file=None,
                timeline=timeline,
                qa=qa,
                ai_report=ai_report,
                voice_file=voice_file,
                warnings=warnings,
            )

        final = self.composer.compose(
            script=plan.script,
            timeline=timeline,
            output_file=root / "final.mp4",
            voice_file=voice_file,
            music_file=music_file,
            burn_subtitles=True,
        )
        return ExecutionResult(
            output_file=str(final),
            timeline=timeline,
            qa=qa,
            ai_report=ai_report,
            voice_file=voice_file,
            warnings=warnings,
        )
