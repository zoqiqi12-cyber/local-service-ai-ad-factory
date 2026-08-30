from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.assets.importer import VideoAssetImporter
from app.jobs.execution import AdExecutionEngine
from app.jobs.pipeline import AdFactoryPipeline, GeneratedAdPlan
from app.models.domain import BusinessProfile
from app.providers.registry import ProviderRegistry


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("本地服务 AI 广告工厂 V1")
        self.resize(980, 760)
        self.asset_folder: str | None = None
        self.output_folder = str(Path("output/ui").resolve())
        self.last_profile: BusinessProfile | None = None
        self.last_plans: list[GeneratedAdPlan] = []
        self.providers = ProviderRegistry()

        self.brand = QLineEdit("示例到家")
        self.city = QLineEdit("中山市")
        self.services = QLineEdit("马桶疏通,地漏疏通,下水道疏通,洗手池疏通")
        self.claims = QLineEdit("本地师傅,专业设备,先报价再施工,价格透明")
        self.language = QLineEdit("普通话")
        self.count = QSpinBox()
        self.count.setRange(1, 100)
        self.count.setValue(5)
        self.duration = QSpinBox()
        self.duration.setRange(10, 60)
        self.duration.setValue(20)

        self.asset_label = QLabel("未选择真实素材文件夹")
        choose_assets = QPushButton("选择真实素材")
        choose_assets.clicked.connect(self.choose_assets)

        self.output_label = QLabel(self.output_folder)
        choose_output = QPushButton("选择输出目录")
        choose_output.clicked.connect(self.choose_output)

        generate = QPushButton("1. 生成广告方案")
        generate.clicked.connect(self.generate)
        execute = QPushButton("2. 生成第1条成片")
        execute.clicked.connect(self.execute_first)

        self.provider_status = QLabel(self._provider_status_text())
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)

        form = QFormLayout()
        form.addRow("品牌", self.brand)
        form.addRow("城市", self.city)
        form.addRow("服务项目", self.services)
        form.addRow("真实卖点", self.claims)
        form.addRow("语言/地方化", self.language)
        form.addRow("生成数量", self.count)
        form.addRow("目标时长", self.duration)

        asset_row = QHBoxLayout()
        asset_row.addWidget(choose_assets)
        asset_row.addWidget(self.asset_label, 1)

        output_row = QHBoxLayout()
        output_row.addWidget(choose_output)
        output_row.addWidget(self.output_label, 1)

        button_row = QHBoxLayout()
        button_row.addWidget(generate)
        button_row.addWidget(execute)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(asset_row)
        layout.addLayout(output_row)
        layout.addWidget(self.provider_status)
        layout.addLayout(button_row)
        layout.addWidget(QLabel("状态 / 生成预览"))
        layout.addWidget(self.preview, 1)

        root = QWidget()
        root.setLayout(layout)
        self.setCentralWidget(root)

    def choose_assets(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "选择施工视频素材文件夹")
        if folder:
            self.asset_folder = folder
            self.asset_label.setText(folder)

    def choose_output(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "选择成片输出目录")
        if folder:
            self.output_folder = folder
            self.output_label.setText(folder)

    def _build_profile(self) -> BusinessProfile:
        return BusinessProfile(
            brand_name=self.brand.text().strip(),
            city=self.city.text().strip(),
            services=self._csv(self.services.text()),
            approved_claims=self._csv(self.claims.text()),
            forbidden_claims=["最低价", "免费上门", "30分钟必到"],
            booking_methods=["私信预约"],
            languages=[self.language.text().strip() or "普通话"],
        )

    def generate(self) -> None:
        try:
            profile = self._build_profile()
            assets = VideoAssetImporter().scan_folder(self.asset_folder) if self.asset_folder else []
            plans = AdFactoryPipeline().generate_plans(
                profile,
                count=self.count.value(),
                duration=self.duration.value(),
                language=self.language.text().strip() or "普通话",
                assets=assets,
            )
            self.last_profile = profile
            self.last_plans = plans
            payload = {
                "profile": profile.model_dump(mode="json"),
                "asset_count": len(assets),
                "provider_status": self.providers.status(),
                "plans": [plan.model_dump() for plan in plans],
            }
            self.preview.setPlainText(json.dumps(payload, ensure_ascii=False, indent=2))
            out = Path(self.output_folder) / "last_plan.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(self.preview.toPlainText(), encoding="utf-8")
        except Exception as exc:
            QMessageBox.critical(self, "生成失败", str(exc))

    def execute_first(self) -> None:
        if not self.last_profile or not self.last_plans:
            QMessageBox.information(self, "请先生成方案", "先点击“生成广告方案”。")
            return
        try:
            result = AdExecutionEngine(self.providers).execute(
                profile=self.last_profile,
                plan=self.last_plans[0],
                output_dir=Path(self.output_folder) / "video-001",
                require_voice=False,
            )
            payload = {
                "output_file": result.output_file,
                "qa_ok": result.qa.ok,
                "errors": result.qa.errors,
                "warnings": result.qa.warnings + result.warnings,
                "provider_status": self.providers.status(),
            }
            self.preview.setPlainText(json.dumps(payload, ensure_ascii=False, indent=2))
            if result.output_file:
                QMessageBox.information(self, "成片完成", f"已输出：\n{result.output_file}")
            else:
                QMessageBox.warning(
                    self,
                    "暂未成片",
                    "当前方案还有缺失 AI 镜头或 Provider 未配置。详情已显示在状态框。",
                )
        except Exception as exc:
            QMessageBox.critical(self, "成片失败", str(exc))

    def _provider_status_text(self) -> str:
        status = self.providers.status()
        return (
            "Provider："
            f"LLM={'已配置' if status['llm'] else '未配置'} | "
            f"TTS={'已配置' if status['tts'] else '未配置'} | "
            f"AI视频={'已配置' if status['video'] else '未配置'}"
        )

    @staticmethod
    def _csv(value: str) -> list[str]:
        return [item.strip() for item in value.replace("，", ",").split(",") if item.strip()]


def run() -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
