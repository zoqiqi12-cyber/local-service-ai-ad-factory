from app.jobs.execution import AdExecutionEngine
from app.jobs.pipeline import AdFactoryPipeline
from app.models.domain import BusinessProfile
from app.providers.registry import ProviderRegistry


def profile() -> BusinessProfile:
    return BusinessProfile(
        brand_name="测试到家",
        city="中山市",
        services=["马桶疏通"],
        approved_claims=["本地师傅", "专业设备"],
        forbidden_claims=["30分钟必到"],
        booking_methods=["私信预约"],
    )


def test_execution_stops_cleanly_when_ai_video_provider_is_missing(tmp_path):
    p = profile()
    plan = AdFactoryPipeline().generate_plans(p, count=1, assets=[])[0]
    result = AdExecutionEngine(ProviderRegistry()).execute(p, plan, tmp_path)
    assert result.output_file is None
    assert not result.qa.ok
    assert any("镜头未生成" in error for error in result.qa.errors)
    assert any("AI Video Provider" in warning for warning in result.warnings)


def test_execution_provider_status_defaults_to_unconfigured():
    status = ProviderRegistry().status()
    assert status == {
        "llm": False,
        "vision": False,
        "tts": False,
        "image": False,
        "video": False,
    }
