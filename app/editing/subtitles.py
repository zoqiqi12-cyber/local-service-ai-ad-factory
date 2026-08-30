from __future__ import annotations

from pathlib import Path

from app.models.domain import AdScript, Timeline


def _srt_time(seconds: float) -> str:
    ms = max(0, int(round(seconds * 1000)))
    hours, ms = divmod(ms, 3_600_000)
    minutes, ms = divmod(ms, 60_000)
    secs, ms = divmod(ms, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


class SubtitleBuilder:
    """Builds SRT subtitles by aligning script lines to timeline clips."""

    def build_srt(self, script: AdScript, timeline: Timeline) -> str:
        line_text = {line.id: line.text for line in script.lines}
        grouped: dict[str, tuple[float, float]] = {}
        for clip in timeline.clips:
            current = grouped.get(clip.line_id)
            if current is None:
                grouped[clip.line_id] = (clip.timeline_start, clip.timeline_end)
            else:
                grouped[clip.line_id] = (min(current[0], clip.timeline_start), max(current[1], clip.timeline_end))

        blocks: list[str] = []
        index = 1
        for line in script.lines:
            if line.id not in grouped:
                continue
            start, end = grouped[line.id]
            blocks.append(
                f"{index}\n{_srt_time(start)} --> {_srt_time(end)}\n{line_text[line.id]}\n"
            )
            index += 1
        return "\n".join(blocks)

    def write(self, script: AdScript, timeline: Timeline, output: str | Path) -> Path:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.build_srt(script, timeline), encoding="utf-8")
        return path
