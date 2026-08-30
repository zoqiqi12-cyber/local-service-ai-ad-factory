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
from app.jobs.pipeline import AdFactoryPipeline
from app.models.domain import BusinessProfile


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("本地服务 AI 广告工厂 V1")
        self.resize(900, 680)
        self.asset_folder: str | None = None

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

        generate = QPushButton("一键生成广告方案")
        generate.clicked.connect(self.generate)
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

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(asset_row)
        layout.addWidget(generate)
        layout.addWidget(QLabel("生成预览"))
        layout.addWidget(self.preview, 1)

        root = QWidget()
        root.setLayout(layout)
        self.setCentralWidget(root)

    def choose_assets(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "选择施工视频素材文件夹")
        if folder:
            self.asset_folder = folder
            self.asset_label.setText(folder)

    def generate(self) -> None:
        try:
            profile = BusinessProfile(
                brand_name=self.brand.text().strip(),
                city=self.city.text().strip(),
                services=self._csv(self.services.text()),
                approved_claims=self._csv(self.claims.text()),
                forbidden_claims=["最低价", "免费上门", "30分钟必到"],
                booking_methods=["私信预约"],
                languages=[self.language.text().strip() or "普通话"],
            )
            assets = (
                VideoAssetImporter().scan_folder(self.asset_folder)
                if self.asset_folder
                else []
            )
            plans = AdFactoryPipeline().generate_plans(
                profile,
                count=self.count.value(),
                duration=self.duration.value(),
                language=self.language.text().strip() or "普通话",
                assets=assets,
            )
            payload = {
                "profile": profile.model_dump(mode="json"),
                "asset_count": len(assets),
                "plans": [plan.model_dump() for plan in plans],
            }
            self.preview.setPlainText(json.dumps(payload, ensure_ascii=False, indent=2))
            out = Path("output/ui_last_plan.json")
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(self.preview.toPlainText(), encoding="utf-8")
        except Exception as exc:
            QMessageBox.critical(self, "生成失败", str(exc))

    @staticmethod
    def _csv(value: str) -> list[str]:
        return [item.strip() for item in value.replace("，", ",").split(",") if item.strip()]


def run() -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
