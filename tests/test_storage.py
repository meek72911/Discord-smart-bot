import pytest
from unittest.mock import MagicMock, patch
import ai_service
import storage


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    db_file = tmp_path / "test_botdata.db"
    monkeypatch.setattr(storage, "DB_PATH", str(db_file))
    monkeypatch.setattr(storage, "_conn", None)
    return db_file


def test_guild_config_roundtrip(tmp_db):
    cfg = storage.get_guild_config(555)
    assert cfg == {"trusted_ids": [], "log_channel_id": None, "watch_enabled": False}

    storage.set_guild_config(555, trusted_ids=[1, 2, 3], log_channel_id=999, watch_enabled=True)
    cfg = storage.get_guild_config(555)
    assert cfg["trusted_ids"] == [1, 2, 3]
    assert cfg["log_channel_id"] == 999
    assert cfg["watch_enabled"] is True


def test_mod_actions_roundtrip(tmp_db):
    storage.record_mod_action(guild_id=42, actor_id=1, target="bob", action="timeout_user", reason="spam")
    rows = storage.recent_mod_actions(42)
    assert len(rows) == 1
    assert rows[0][3] == "timeout_user"
    assert rows[0][2] == "bob"


def test_user_lang_roundtrip(tmp_db):
    assert storage.get_user_lang(10) is None
    storage.set_user_lang(10, "spanish")
    assert storage.get_user_lang(10) == "spanish"
    storage.set_user_lang(10, "french")
    assert storage.get_user_lang(10) == "french"


def test_channel_memory_roundtrip_and_cap(tmp_db):
    hist = [{"role": "user", "parts": [{"text": f"msg {i}"}]} for i in range(60)]
    storage.save_channel_history(31, hist)

    loaded = storage.load_channel_history(31)
    assert len(loaded) == 40  # capped at last 40

    storage.delete_channel_memory(31)
    assert storage.load_channel_history(31) == []


def test_verdict_schema_fields():
    v = ai_service.ModerationVerdict(
        violation=True,
        categories=["harassment"],
        severity=6,
        confidence=0.9,
        reason="insults a user",
    )
    assert v.violation is True
    assert 0 <= v.severity <= 10
