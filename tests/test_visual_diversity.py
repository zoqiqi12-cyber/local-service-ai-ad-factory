from app.assets.matcher import AssetMatcher
from app.assets.visual_fingerprint import VisualFingerprintExtractor
from app.models.domain import AssetShot, ShotRequirement


def test_visual_fingerprint_similarity_uses_bit_hamming_distance():
    a = "0" * 64
    b = "0" * 63 + "1"
    c = "f" * 64
    assert VisualFingerprintExtractor.distance(a, a) == 0
    assert VisualFingerprintExtractor.distance(a, b) == 1
    assert VisualFingerprintExtractor.similarity(a, b) > 0.99
    assert VisualFingerprintExtractor.similarity(a, c) == 0.0


def test_matcher_penalizes_near_duplicate_selected_shot():
    req = ShotRequirement(
        line_id="L1",
        semantic_intent=["hook", "problem"],
        content_tags=["马桶疏通", "blockage"],
        min_duration=0.4,
        max_duration=1.0,
    )
    selected = AssetShot(
        id="old",
        source_file="a.mp4",
        start=0,
        end=2,
        content_tags=["马桶疏通", "blockage"],
        quality_score=70,
        hook_score=80,
        motion_score=70,
        visual_fingerprint="0" * 64,
    )
    duplicate = AssetShot(
        id="dup",
        source_file="b.mp4",
        start=0,
        end=2,
        content_tags=["马桶疏通", "blockage"],
        quality_score=90,
        hook_score=90,
        motion_score=80,
        visual_fingerprint="0" * 63 + "1",
    )
    diverse = AssetShot(
        id="diverse",
        source_file="c.mp4",
        start=0,
        end=2,
        content_tags=["马桶疏通", "blockage"],
        quality_score=75,
        hook_score=75,
        motion_score=65,
        visual_fingerprint="f" * 64,
    )
    matcher = AssetMatcher()
    assert matcher.best(req, [duplicate, diverse], selected=[selected]).id == "diverse"


def test_result_phase_rewards_stable_clear_shot():
    req = ShotRequirement(
        line_id="L4",
        semantic_intent=["proof", "result", "success"],
        content_tags=["success_flow", "after"],
        min_duration=0.5,
        max_duration=2.0,
    )
    shaky = AssetShot(
        id="shaky",
        source_file="shaky.mp4",
        start=0,
        end=3,
        content_tags=["success_flow", "after"],
        quality_score=60,
        result_score=90,
        stability_score=10,
        sharpness_score=30,
    )
    stable = AssetShot(
        id="stable",
        source_file="stable.mp4",
        start=0,
        end=3,
        content_tags=["success_flow", "after"],
        quality_score=75,
        result_score=85,
        stability_score=95,
        sharpness_score=90,
    )
    assert AssetMatcher().best(req, [shaky, stable]).id == "stable"
