import shutil
from pathlib import Path

import pytest

from coach import create_app
from coach.config import Config

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def base_dir(tmp_path):
    shutil.copytree(REPO_ROOT / "plans", tmp_path / "plans")
    return tmp_path


@pytest.fixture
def config(base_dir):
    return Config(base_dir=base_dir, ai_enabled=False)


@pytest.fixture
def app(config):
    app = create_app(config)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def fixtures_dir():
    return FIXTURES
