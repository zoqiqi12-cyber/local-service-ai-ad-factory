from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.models.domain import Timeline, TimelineClip


class VideoGenerationProvider(Protocol):
    def generate(self, prompt: str, duration: float, aspect_ratio: str = "9:16") -> str:
        """Return a local file path for the generated video."""
        ...


@dataclass
class ResolveReport:
    resolved: int
    remaining: int


class AIPendingResolver:
    """Replaces ai_pending timeline clips with generated local video files."""

    def resolve(self, timeline: Timeline, provider: VideoGenerationProvider) -> tuple[Timeline, ResolveReport]:
        clips: list[TimelineClip] = []
        resolved = 0
        for clip in timeline.clips:
            if clip.source_type != "ai_pending":
                clips.append(clip)
                continue
            if not clip.generation_prompt:
                clips.append(clip)
                continue
            duration = max(0.2, clip.timeline_end - clip.timeline_start)
            generated = provider.generate(clip.generation_prompt, duration=duration, aspect_ratio="9:16")
            if not generated or not Path(generated).exists():
                clips.append(clip)
                continue
            clips.append(
                clip.model_copy(
                    update={
                        "source_file": generated,
                        "source_start": 0.0,
                        "source_end": duration,
                        "source_type": "ai_generated",
                    }
                )
            )
            resolved += 1

        updated = timeline.model_copy(update={"clips": clips})
        remaining = sum(1 for c in clips if c.source_type == "ai_pending")
        return updated, ResolveReport(resolved=resolved, remaining=remaining)
