from app.editing.subtitles import SubtitleBuilder
from app.models.domain import (
    AdDNA,
    AdScript,
    BusinessProfile,
    CreativeMode,
    HookType,
    ScriptLine,
    Timeline,
    TimelineClip,
)
from app.qa.validator import AdQAValidator
from app.voice.narration import NarrationEngine


def sample_script() -> AdScript:
    dna = AdDNA(
        strategy_id="A08",
        hook_type=HookType.PRICE,
        pain="马桶堵塞",
        service="马桶疏通",
        selling_points=["先报价再施工"],
        proof=["真实施工"],
        trust=["价格透明"],
        cta="私信预约",
        creative_mode=CreativeMode.HYBRID,
        target_duration=3,
    )
    return AdScript(
        dna=dna,
        language="普通话",
        locale="中山市",
        lines=[
            ScriptLine(id="1", role="hook", text="马桶堵了别着急", semantic_intent=["hook", "pain"]),
            ScriptLine(id="2", role="solution", text="先报价再施工", semantic_intent=["proof"]),
        ],
        claims_used=["先报价再施工"],
    )


def sample_timeline(source_type="real") -> Timeline:
    return Timeline(
        duration=3.0,
        voice_language="普通话",
        title="测试",
        clips=[
            TimelineClip(line_id="1", timeline_start=0, timeline_end=1.2, source_type=source_type, source_file="a.mp4" if source_type != "ai_pending" else None),
            TimelineClip(line_id="2", timeline_start=1.2, timeline_end=3.0, source_type="real", source_file="b.mp4"),
        ],
    )


def test_subtitles_follow_timeline():
    srt = SubtitleBuilder().build_srt(sample_script(), sample_timeline())
    assert "00:00:00,000 --> 00:00:01,200" in srt
    assert "马桶堵了别着急" in srt


def test_qa_blocks_pending_ai():
    profile = BusinessProfile(
        brand_name="测试到家", city="中山市", services=["马桶疏通"], approved_claims=["先报价再施工"]
    )
    result = AdQAValidator().validate(profile, sample_script(), sample_timeline("ai_pending"))
    assert not result.ok
    assert any("镜头未生成" in message for message in result.errors)


def test_narration_combines_localized_lines():
    text = NarrationEngine().script_text(sample_script())
    assert "马桶堵了别着急" in text
    assert "先报价再施工" in text
