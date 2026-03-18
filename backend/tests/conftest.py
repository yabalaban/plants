import os
import pytest
import tempfile


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")


@pytest.fixture
def env_db_path(db_path, monkeypatch):
    monkeypatch.setenv("PLANTS_DB_PATH", db_path)
    return db_path
