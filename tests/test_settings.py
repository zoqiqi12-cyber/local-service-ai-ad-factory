from app.providers.registry import ProviderRegistry
from app.settings import ProviderSettings, SettingsStore


def test_settings_round_trip(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")
    original = ProviderSettings(
        llm_url="https://example.test/llm",
        llm_api_key="secret",
        vision_url="https://example.test/vision",
        tts_languages="普通话",
        tts_dialects="粤语,中山口语",
        video_max_seconds="8",
    )
    store.save(original)
    loaded = store.load()
    assert loaded.llm_url == original.llm_url
    assert loaded.llm_api_key == "secret"
    assert loaded.tts_dialects == "粤语,中山口语"


def test_registry_can_load_local_settings(tmp_path, monkeypatch):
    for name in (
        "AD_FACTORY_LLM_URL",
        "AD_FACTORY_LLM_API_KEY",
        "AD_FACTORY_VISION_ENDPOINT",
        "AD_FACTORY_VISION_API_KEY",
        "AD_FACTORY_TTS_ENDPOINT",
        "AD_FACTORY_TTS_API_KEY",
        "AD_FACTORY_VIDEO_ENDPOINT",
        "AD_FACTORY_VIDEO_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)

    store = SettingsStore(tmp_path / "settings.json")
    store.save(ProviderSettings(llm_url="https://example.test/llm"))
    registry = ProviderRegistry.from_local_settings(store)
    assert registry.llm is not None
    assert registry.vision is None
    assert registry.tts is None
    assert registry.video is None
