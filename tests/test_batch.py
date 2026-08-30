from app.jobs.batch import BatchExecutionEngine
from app.jobs.pipeline import AdFactoryPipeline
from app.models.domain import BusinessProfile
from app.providers.registry import ProviderRegistry


def test_batch_keeps_each_failure_isolated(tmp_path):
    profile = BusinessProfile(
        brand_name="测试到家",
        city="中山市",
        services=["马桶疏通", "地漏疏通"],
        approved_claims=["本地师傅"],
        booking_methods=["私信预约"],
    )
    plans = AdFactoryPipeline().generate_plans(profile, count=3, assets=[])
    result = BatchExecutionEngine(ProviderRegistry()).execute(profile, plans, tmp_path)
    assert len(result.items) == 3
    assert result.success_count == 0
    assert result.failure_count == 3
    assert all(item.error for item in result.items)
