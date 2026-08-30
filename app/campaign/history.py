from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.models.domain import AdDNA, AdScript, Timeline


def dna_fingerprint(dna: AdDNA) -> str:
    parts = [
        dna.strategy_id,
        dna.hook_type.value,
        dna.service,
        dna.fear or "",
        ",".join(sorted(dna.selling_points)),
        ",".join(sorted(dna.proof)),
        dna.cta,
        dna.creative_mode.value,
    ]
    return "|".join(parts)


def script_fingerprint(script: AdScript) -> str:
    normalized = "|".join("".join(line.text.split()) for line in script.lines)
    return f"{dna_fingerprint(script.dna)}::{normalized}"


@dataclass
class HistoryEntry:
    dna_fingerprint: str
    script_fingerprint: str
    title: str
    asset_ids: list[str]


class CampaignHistory:
    """Small JSONL memory used to reduce repetition between generation batches."""

    def __init__(self, path: str | Path = "output/campaign_history.jsonl") -> None:
        self.path = Path(path).expanduser().resolve()

    def recent(self, limit: int = 300) -> list[HistoryEntry]:
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()[-limit:]
        entries: list[HistoryEntry] = []
        for line in lines:
            try:
                payload = json.loads(line)
                entries.append(HistoryEntry(**payload))
            except (json.JSONDecodeError, TypeError):
                continue
        return entries

    def seen_dna(self, limit: int = 300) -> set[str]:
        return {entry.dna_fingerprint for entry in self.recent(limit)}

    def record(self, script: AdScript, timeline: Timeline) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        entry = HistoryEntry(
            dna_fingerprint=dna_fingerprint(script.dna),
            script_fingerprint=script_fingerprint(script),
            title=timeline.title,
            asset_ids=[clip.asset_id for clip in timeline.clips if clip.asset_id],
        )
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry.__dict__, ensure_ascii=False) + "\n")
