from app.jobs.pipeline import AdFactoryPipeline
from app.models.domain import BusinessProfile


def profile() -> BusinessProfile:
    return BusinessProfile(
        brand_name="测试到家",
        city="中山市",
        services=["马桶疏通", "下水道疏通"],
        approved_claims=["本地师傅", "先报价再施工"],
        forbidden_claims=["30分钟必到"],
        booking_methods=["私信预约"],
    )


def test_pipeline_generates_requested_count():
    plans = AdFactoryPipeline().generate_plans(profile(), count=4)
    assert len(plans) == 4
    assert all(plan.script.lines for plan in plans)
    assert all(plan.shots for plan in plans)


def test_script_claims_are_whitelisted():
    p = profile()
    plans = AdFactoryPipeline().generate_plans(p, count=8)
    allowed = set(p.approved_claims) - set(p.forbidden_claims)
    for plan in plans:
        assert set(plan.script.claims_used).issubset(allowed)


def test_unknown_dialect_falls_back_safely():
    plan = AdFactoryPipeline().generate_plans(profile(), count=1, language="不存在的方言")[0]
    assert "回退普通话文本" in plan.script.language
