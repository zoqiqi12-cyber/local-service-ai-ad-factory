from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.models.domain import Timeline, TimelineClip
from app.providers.base import VideoProvider


@dataclass
class ResolveReport:
    resolved: int
    remaining: int
    generated_files: list[str]


class AIPendingResolver:
    """Replace ai_pending clips using the configured VideoProvider."""

    def resolve(
        self,
        timeline: Timeline,
        provider: VideoProvider,
        output_dir: str | Path,
    ) -> tuple[Timeline, ResolveReport]:
        root = Path(output_dir).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)

        clips: list[TimelineClip] = []
        generated_files: list[str] = []
        resolved = 0
        for index, clip in enumerate(timeline.clips):
            if clip.source_type != "ai_pending":
                clips.append(clip)
                continue
            if not clip.generation_prompt:
                clips.append(clip)
                continue

            duration = max(0.2, clip.timeline_end - clip.timeline_start)
            target = root / f"ai-shot-{index:04d}.mp4"
            generated = provider.generate(
                prompt=clip.generation_prompt,
                duration=duration,
                output_path=str(target),
            )
            path = Path(generated).expanduser().resolve() if generated else target
            if not path.exists():
                clips.append(clip)
                continue

            generated_files.append(str(path))
            clips.append(
                clip.model_copy(update={
                    "source_file": str(path),
                    "source_start": 0.0,
                    "source_end": duration,
                    "source_type": "ai_generated",
                })
            )
            resolved += 1

        updated = timeline.model_copy(update={"clips": clips})
        remaining = sum(1 for c in clips if c.source_type == "ai_pending")
        return updated, ResolveReport(
            resolved=resolved,
            remaining=remaining,
            generated_files=generated_files,
        )
