from pathlib import Path

from app.assets.importer import VideoAssetImporter
from app.models.domain import AssetShot


def test_importer_uses_scene_splitter_when_available(tmp_path, monkeypatch):
    video = tmp_path / "马桶堵塞.mp4"
    video.write_bytes(b"x")
    importer = VideoAssetImporter(analyze_visuals=False, split_scenes=True)
    monkeypatch.setattr(importer, "probe_duration", lambda path: 5.0)
    monkeypatch.setattr(
        importer.splitter,
        "split",
        lambda path: [
            AssetShot(id="s1", source_file=str(path), start=0.0, end=1.0, quality_score=50),
            AssetShot(id="s2", source_file=str(path), start=1.0, end=3.0, quality_score=50),
        ],
    )
    shots = importer.scan_folder(tmp_path)
    assert [shot.id for shot in shots] == ["s1", "s2"]
    assert "toilet" in shots[0].content_tags
    assert "blockage" in shots[0].content_tags


def test_importer_falls_back_to_full_video_when_split_fails(tmp_path, monkeypatch):
    video = tmp_path / "ordinary.mp4"
    video.write_bytes(b"x")
    importer = VideoAssetImporter(analyze_visuals=False, split_scenes=True)
    monkeypatch.setattr(importer, "probe_duration", lambda path: 4.25)

    def fail(path):
        raise ValueError("bad scene data")

    monkeypatch.setattr(importer.splitter, "split", fail)
    shots = importer.scan_folder(tmp_path)
    assert len(shots) == 1
    assert shots[0].start == 0.0
    assert shots[0].end == 4.25
