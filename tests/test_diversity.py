from app.campaign.brain import CampaignBrain
from app.campaign.history import CampaignHistory, dna_fingerprint
from app.director.engine import DirectorEngine
from app.models.domain import BusinessProfile
from app.script.engine import ScriptEngine


def profile() -> BusinessProfile:
    return BusinessProfile(
        brand_name="测试到家",
        city="中山市",
        services=["马桶疏通", "地漏疏通", "下水道疏通"],
        approved_claims=["本地师傅", "专业设备", "先报价再施工", "价格透明"],
        booking_methods=["私信预约", "平台预约"],
    )


def test_campaign_brain_prefers_unseen_dna():
    brain = CampaignBrain()
    first = brain.build_matrix(profile(), count=8)
    seen = {dna_fingerprint(dna) for dna in first}
    second = brain.build_matrix(profile(), count=8, seen_fingerprints=seen)
    assert all(dna_fingerprint(dna) not in seen for dna in second)


def test_fast_cut_director_creates_multiple_shots_per_line():
    dna = CampaignBrain().build_matrix(profile(), count=20)
    fast = next(item for item in dna if item.creative_mode.value == "fast_cut")
    script = ScriptEngine().generate(profile(), fast)
    shots = DirectorEngine().plan(script)
    hook_shots = [shot for shot in shots if shot.line_id == "L1"]
    assert len(hook_shots) >= 2
    assert max(shot.max_duration for shot in hook_shots) <= 0.85


def test_campaign_history_roundtrip(tmp_path):
    history = CampaignHistory(tmp_path / "history.jsonl")
    dna = CampaignBrain().build_matrix(profile(), count=1)[0]
    script = ScriptEngine().generate(profile(), dna)
    from app.models.domain import Timeline

    history.record(script, Timeline(duration=1.0, clips=[], voice_language="普通话", title="测试"))
    assert dna_fingerprint(dna) in history.seen_dna()
