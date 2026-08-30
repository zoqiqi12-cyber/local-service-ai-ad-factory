from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from app.settings import ProviderSettings, SettingsStore


class ProviderSettingsDialog(QDialog):
    def __init__(self, store: SettingsStore | None = None, parent=None) -> None:
        super().__init__(parent)
        self.store = store or SettingsStore()
        self.setWindowTitle("AI 服务设置")
        self.resize(720, 520)
        current = self.store.load()

        self.llm_url = QLineEdit(current.llm_url)
        self.llm_key = self._secret(current.llm_api_key)
        self.vision_url = QLineEdit(current.vision_url)
        self.vision_key = self._secret(current.vision_api_key)
        self.tts_url = QLineEdit(current.tts_url)
        self.tts_key = self._secret(current.tts_api_key)
        self.tts_languages = QLineEdit(current.tts_languages)
        self.tts_dialects = QLineEdit(current.tts_dialects)
        self.video_url = QLineEdit(current.video_url)
        self.video_key = self._secret(current.video_api_key)
        self.video_max_seconds = QLineEdit(current.video_max_seconds)

        form = QFormLayout()
        form.addRow("脚本 LLM 地址", self.llm_url)
        form.addRow("脚本 LLM API Key", self.llm_key)
        form.addRow("视觉 AI 地址", self.vision_url)
        form.addRow("视觉 AI API Key", self.vision_key)
        form.addRow("TTS 地址", self.tts_url)
        form.addRow("TTS API Key", self.tts_key)
        form.addRow("TTS 语言", self.tts_languages)
        form.addRow("TTS 方言", self.tts_dialects)
        form.addRow("AI 视频地址", self.video_url)
        form.addRow("AI 视频 API Key", self.video_key)
        form.addRow("AI 视频单镜头最长秒数", self.video_max_seconds)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_and_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("API Key 只保存在这台电脑的用户目录，不会提交到 GitHub。环境变量仍可覆盖这里的设置。"))
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

    @staticmethod
    def _secret(value: str) -> QLineEdit:
        field = QLineEdit(value)
        field.setEchoMode(QLineEdit.Password)
        return field

    def save_and_accept(self) -> None:
        self.store.save(
            ProviderSettings(
                llm_url=self.llm_url.text().strip(),
                llm_api_key=self.llm_key.text().strip(),
                vision_url=self.vision_url.text().strip(),
                vision_api_key=self.vision_key.text().strip(),
                tts_url=self.tts_url.text().strip(),
                tts_api_key=self.tts_key.text().strip(),
                tts_languages=self.tts_languages.text().strip() or "普通话",
                tts_dialects=self.tts_dialects.text().strip(),
                video_url=self.video_url.text().strip(),
                video_api_key=self.video_key.text().strip(),
                video_max_seconds=self.video_max_seconds.text().strip() or "10",
            )
        )
        self.accept()
