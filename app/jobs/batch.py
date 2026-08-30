from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.jobs.execution import AdExecutionEngine, ExecutionResult
from app.jobs.pipeline import GeneratedAdPlan
from app.models.domain import BusinessProfile
from app.providers.registry import ProviderRegistry


@dataclass
class BatchItemResult:
    index: int
    ok: bool
    output_file: str | None = None
    error: str | None = None
    execution: ExecutionResult | None = None


@dataclass
class BatchResult:
    items: list[BatchItemResult] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        return sum(1 for item in self.items if item.ok)

    @property
    def failure_count(self) -> int:
        return sum(1 for item in self.items if not item.ok)


class BatchExecutionEngine:
    """Execute many ads into isolated output folders.

    Batch failures are isolated by default so a single bad AI generation does not
    discard the rest of a 50/100-video job.
    """

    def __init__(self, providers: ProviderRegistry | None = None) -> None:
        self.providers = providers or ProviderRegistry()

    def execute(
        self,
        profile: BusinessProfile,
        plans: list[GeneratedAdPlan],
        output_dir: str | Path,
        music_file: str | Path | None = None,
        continue_on_error: bool = True,
    ) -> BatchResult:
        root = Path(output_dir).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        engine = AdExecutionEngine(self.providers)
        result = BatchResult()

        for index, plan in enumerate(plans, start=1):
            item_dir = root / f"video-{index:03d}"
            try:
                execution = engine.execute(
                    profile=profile,
                    plan=plan,
                    output_dir=item_dir,
                    music_file=music_file,
                    require_voice=False,
                )
                ok = bool(execution.output_file) and execution.qa.ok
                result.items.append(
                    BatchItemResult(
                        index=index,
                        ok=ok,
                        output_file=execution.output_file,
                        error=None if ok else "; ".join(execution.qa.errors + execution.warnings),
                        execution=execution,
                    )
                )
            except Exception as exc:
                result.items.append(BatchItemResult(index=index, ok=False, error=str(exc)))
                if not continue_on_error:
                    raise
        return result
