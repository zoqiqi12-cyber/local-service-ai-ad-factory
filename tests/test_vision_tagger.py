from app.assets.vision_tagger import VisionAssetTagger
from app.models.domain import AssetShot
from app.providers.base import ProviderCapabilities, VisionProvider


class FakeVision(VisionProvider):
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(supports_vision=True)

    def analyze(self, image_bytes: bytes, prompt: str, schema: dict) -> dict:
        assert image_bytes
        return {
            "content_tags": ["toilet", "blockage", "invented_claim"],
            "semantic_tags": ["problem", "urgent", "fake_semantic"],
            "hook_score": 91,
            "urgency_score": 88,
            "proof_score": -20,
            "result_score": 150,
        }


def test_vision_tagger_filters_unknown_labels_and_clamps_scores(monkeypatch):
    shot = AssetShot(id="s1", source_file="missing.mp4", start=0, end=1)
    tagger = VisionAssetTagger(FakeVision())
    monkeypatch.setattr(tagger, "_frame_bytes", lambda _: b"jpeg")

    tagged = tagger.tag(shot)

    assert "toilet" in tagged.content_tags
    assert "blockage" in tagged.content_tags
    assert "invented_claim" not in tagged.content_tags
    assert "problem" in tagged.semantic_tags
    assert "fake_semantic" not in tagged.semantic_tags
    assert tagged.hook_score == 91
    assert tagged.urgency_score == 88
    assert tagged.proof_score == 0
    assert tagged.result_score == 100
