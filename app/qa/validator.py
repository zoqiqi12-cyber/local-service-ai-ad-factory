from __future__ import annotations

from dataclasses import dataclass, field

from app.models.domain import AdScript, BusinessProfile, Timeline


@dataclass
class QAResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class AdQAValidator:
    """Cheap deterministic checks before expensive rendering or publishing."""

    def validate(self, profile: BusinessProfile, script: AdScript, timeline: Timeline) -> QAResult:
        errors: list[str] = []
        warnings: list[str] = []

        allowed = set(profile.approved_claims) - set(profile.forbidden_claims)
        illegal_claims = [claim for claim in script.claims_used if claim not in allowed]
        if illegal_claims:
            errors.append(f"脚本使用未授权宣传词: {', '.join(illegal_claims)}")

        text = " ".join(line.text for line in script.lines)
        for forbidden in profile.forbidden_claims:
            if forbidden and forbidden in text:
                errors.append(f"脚本文案包含禁用宣传词: {forbidden}")

        pending = sum(1 for clip in timeline.clips if clip.source_type == "ai_pending")
        if pending:
            errors.append(f"仍有 {pending} 个 AI 镜头未生成")

        if not timeline.clips:
            errors.append("时间轴为空")
        if timeline.duration <= 0:
            errors.append("成片时长无效")
        if abs(timeline.duration - script.dna.target_duration) > max(5, script.dna.target_duration * 0.4):
            warnings.append(
                f"时间轴 {timeline.duration:.1f}s 与目标 {script.dna.target_duration}s 差异较大"
            )

        seen: dict[str, int] = {}
        for clip in timeline.clips:
            if clip.asset_id:
                seen[clip.asset_id] = seen.get(clip.asset_id, 0) + 1
        repeated = [asset_id for asset_id, count in seen.items() if count >= 3]
        if repeated:
            warnings.append(f"同一镜头重复使用过多: {', '.join(repeated)}")

        return QAResult(ok=not errors, errors=errors, warnings=warnings)
