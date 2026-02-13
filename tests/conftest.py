import json
from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir():
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_landmarks(fixtures_dir):
    with open(fixtures_dir / "sample_landmarks.json") as f:
        return json.load(f)


@pytest.fixture
def ideal_ranges():
    config_path = Path(__file__).parent.parent / "config" / "ideal_ranges.json"
    with open(config_path) as f:
        return json.load(f)
