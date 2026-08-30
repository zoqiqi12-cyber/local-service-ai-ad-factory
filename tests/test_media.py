import pytest

from app.editing.renderer import FFmpegRenderer
from app.models.domain import Timeline, TimelineClip


def test_renderer_rejects_unresolved_ai_clip():
    timeline = Timeline(
        duration=1.2,
        voice_language="普通话",
        title="测试",
        clips=[
            TimelineClip(
                line_id="hook-1",
                timeline_start=0,
                timeline_end=1.2,
                source_type="ai_pending",
                generation_prompt="test",
            )
        ],
    )
    with pytest.raises(ValueError, match="unresolved AI clips"):
        FFmpegRenderer().render(timeline, "output/test.mp4")
