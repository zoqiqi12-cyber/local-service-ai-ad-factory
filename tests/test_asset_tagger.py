from app.assets.tagger import HeuristicAssetTagger
from app.models.domain import AssetShot


def test_filename_tagger_builds_ad_semantics():
    shot = AssetShot(
        id="s1",
        source_file="素材/马桶返水严重_师傅疏通机施工.mp4",
        start=0,
        end=2.5,
    )
    tagged = HeuristicAssetTagger().tag(shot)
    assert "toilet" in tagged.content_tags
    assert "dirty_water" in tagged.content_tags
    assert "machine" in tagged.content_tags
    assert "problem" in tagged.semantic_tags
    assert "proof" in tagged.semantic_tags
    assert tagged.hook_score >= 62
    assert tagged.proof_score >= 65


def test_success_shot_gets_result_score():
    shot = AssetShot(
        id="s2",
        source_file="马桶疏通后排水畅通效果.mp4",
        start=1,
        end=4,
    )
    tagged = HeuristicAssetTagger().tag(shot)
    assert "success_flow" in tagged.content_tags
    assert "result" in tagged.semantic_tags
    assert tagged.result_score >= 75
