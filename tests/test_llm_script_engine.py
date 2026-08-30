from app.campaign.brain import CampaignBrain
from app.jobs.pipeline import AdFactoryPipeline
from app.models.domain import BusinessProfile
from app.providers.base import LLMProvider
from app.providers.registry import ProviderRegistry


class FakeLLM(LLMProvider):
    def generate_json(self, system_prompt: str, user_prompt: str, schema: dict) -> dict:
        return {
            "lines": [
                {"role": "hook", "text": "中山下水道突然堵了？", "semantic_intent": ["hook", "problem"]},
                {"role": "pain", "text": "返水、排水慢都很影响使用。", "semantic_intent": ["pain"]},
                {"role": "solution", "text": "测试到家可安排本地师傅处理。", "semantic_intent": ["solution", "professional"]},
                {"role": "proof", "text": "施工过程和疏通结果都能直观看到。", "semantic_intent": ["proof", "result"]},
                {"role": "cta", "text": "需要时可私信预约。", "semantic_intent": ["cta"]},
            ],
            "title_candidates": ["中山下水道疏通"],
            "claims_used": ["本地师傅", "AI自己编的保证"],
        }


class UnsafeLLM(LLMProvider):
    def generate_json(self, system_prompt: str, user_prompt: str, schema: dict) -> dict:
        return {
            "lines": [
                {"role": "hook", "text": "中山30分钟必到，马上处理！", "semantic_intent": ["hook"]},
                {"role": "pain", "text": "管道堵了。", "semantic_intent": ["pain"]},
                {"role": "solution", "text": "安排师傅。", "semantic_intent": ["solution"]},
                {"role": "cta", "text": "私信预约。", "semantic_intent": ["cta"]},
            ],
            "title_candidates": [],
            "claims_used": [],
        }


def profile() -> BusinessProfile:
    return BusinessProfile(
        brand_name="测试到家",
        city="中山市",
        services=["下水道疏通"],
        approved_claims=["本地师傅", "先报价再施工"],
        forbidden_claims=["30分钟必到"],
        booking_methods=["私信预约"],
    )


def test_pipeline_uses_llm_and_filters_unapproved_claims():
    registry = ProviderRegistry(llm=FakeLLM())
    plan = AdFactoryPipeline(registry).generate_plans(profile(), count=1)[0]
    assert "中山下水道突然堵了" in plan.script.lines[0].text
    assert plan.script.claims_used == ["本地师傅"]


def test_unsafe_llm_falls_back_to_template():
    registry = ProviderRegistry(llm=UnsafeLLM())
    plan = AdFactoryPipeline(registry).generate_plans(profile(), count=1)[0]
    text = " ".join(line.text for line in plan.script.lines)
    assert "30分钟必到" not in text
    assert "测试到家" in text
