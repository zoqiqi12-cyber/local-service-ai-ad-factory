from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.assets.importer import VideoAssetImporter
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
    parser = argparse.ArgumentParser(description="本地服务 AI 广告工厂 V1")
    parser.add_argument("--city", default="中山市")
    parser.add_argument("--count", type=int, default=3)
    parser.add_argument("--duration", type=int, default=20)
    parser.add_argument("--language", default="普通话")
    parser.add_argument("--assets", help="本地施工视频素材文件夹")
    parser.add_argument("--output", default="output/ad_plans.json")
    args = parser.parse_args()

    profile = build_demo_profile(args.city)
    assets = VideoAssetImporter().scan_folder(args.assets) if args.assets else []
    plans = AdFactoryPipeline().generate_plans(
        profile=profile,
        count=args.count,
        duration=args.duration,
        language=args.language,
        assets=assets,
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "profile": profile.model_dump(mode="json"),
        "asset_count": len(assets),
        "assets": [asset.model_dump(mode="json") for asset in assets],
        "plans": [plan.model_dump() for plan in plans],
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已生成 {len(plans)} 条广告方案 -> {output}")
    print(f"已扫描 {len(assets)} 个真实视频素材")


if __name__ == "__main__":
    main()
