from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.jobs.pipeline import AdFactoryPipeline
from app.models.domain import BusinessProfile


def build_demo_profile(city: str) -> BusinessProfile:
    return BusinessProfile(
        brand_name="示例到家",
        city=city,
        services=["马桶疏通", "地漏疏通", "下水道疏通", "洗手池疏通"],
        approved_claims=["本地师傅", "专业设备", "先报价再施工", "价格透明"],
        forbidden_claims=["免费上门", "最低价", "30分钟必到"],
        booking_methods=["私信预约"],
        languages=["普通话", "中山口语"],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Local Service AI Ad Factory V1 demo")
    parser.add_argument("--city", default="中山市")
    parser.add_argument("--count", type=int, default=3)
    parser.add_argument("--duration", type=int, default=20)
    parser.add_argument("--language", default="普通话")
    parser.add_argument("--output", default="output/ad_plans.json")
    args = parser.parse_args()

    profile = build_demo_profile(args.city)
    plans = AdFactoryPipeline().generate_plans(
        profile=profile,
        count=args.count,
        duration=args.duration,
        language=args.language,
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "profile": profile.model_dump(mode="json"),
        "plans": [plan.model_dump() for plan in plans],
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated {len(plans)} ad plans -> {output}")


if __name__ == "__main__":
    main()
