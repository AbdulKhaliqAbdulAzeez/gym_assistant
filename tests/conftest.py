import pytest


@pytest.fixture(autouse=True)
def _disable_storage(monkeypatch: pytest.MonkeyPatch):
    """Disable persistence during tests by default."""
    monkeypatch.setenv("GYM_ASSISTANT_DISABLE_STORAGE", "true")
    yield
