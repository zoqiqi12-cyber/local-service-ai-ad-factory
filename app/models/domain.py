from __future__ import annotations

from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field


class HookType(str, Enum):
    LOCAL = "local"
    PAIN = "pain"
    URGENT = "urgent"
    TIME = "time"
    PRICE = "price"
    CURIOSITY = "curiosity"


class CreativeMode(str, Enum):
    SPOKESPERSON = "spokesperson"
    REAL_WORK = "real_work"
    FAST_CUT = "fast_cut"
    AI_PERSON = "ai_person"
    AI_SCENE = "ai_scene"
    GRAPHIC = "graphic"
    HYBRID = "hybrid"


class BusinessProfile(BaseModel):
    brand_name: str
    industry: str = "管道疏通"
    city: str
    districts: list[str] = Field(default_factory=list)
    services: list[str]
    approved_claims: list[str] = Field(default_factory=list)
    forbidden_claims: list[str] = Field(default_factory=list)
    booking_methods: list[str] = Field(default_factory=lambda: ["私信预约"])
    languages: list[str] = Field(default_factory=lambda: ["普通话"])


class AdDNA(BaseModel):
    strategy_id: str
    hook_type: HookType
    pain: str
    fear: str | None = None
    service: str
    selling_points: list[str] = Field(default_factory=list)
    proof: list[str] = Field(default_factory=list)
    trust: list[str] = Field(default_factory=list)
    cta: str
    creative_mode: CreativeMode = CreativeMode.HYBRID
    target_duration: int = 20


class ScriptLine(BaseModel):
    id: str
    role: Literal["hook", "pain", "solution", "proof", "benefit", "cta"]
    text: str
    semantic_intent: list[str] = Field(default_factory=list)


class AdScript(BaseModel):
    dna: AdDNA
    language: str
    locale: str
    lines: list[ScriptLine]
    title_candidates: list[str] = Field(default_factory=list)
    claims_used: list[str] = Field(default_factory=list)


class ShotRequirement(BaseModel):
    line_id: str
    semantic_intent: list[str]
    content_tags: list[str]
    emotion: str | None = None
    time_of_day: str | None = None
    preferred_source: Literal["real", "ai", "either"] = "real"
    min_duration: float = 0.4
    max_duration: float = 2.0
    generation_prompt: str | None = None


class AssetShot(BaseModel):
    id: str
    source_file: str
    start: float
    end: float
    content_tags: list[str] = Field(default_factory=list)
    semantic_tags: list[str] = Field(default_factory=list)
    quality_score: float = 0
    motion_score: float = 0
    stability_score: float = 0
    sharpness_score: float = 0
    hook_score: float = 0
    urgency_score: float = 0
    proof_score: float = 0
    result_score: float = 0
    visual_fingerprint: str | None = None
    used_count: int = 0

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


class TimelineClip(BaseModel):
    line_id: str
    asset_id: str | None = None
    source_file: str | None = None
    source_start: float | None = None
    source_end: float | None = None
    timeline_start: float
    timeline_end: float
    source_type: Literal["real", "ai_pending", "ai_generated"]
    generation_prompt: str | None = None


class Timeline(BaseModel):
    duration: float
    clips: list[TimelineClip]
    voice_language: str
    title: str
