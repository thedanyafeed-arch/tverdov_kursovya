"""Корневые фикстуры pytest для всего проекта."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "e2e: E2E Django (FastAPI + Django должны быть запущены)",
    )


def pytest_collection_modifyitems(config, items):
    if os.getenv("SKIP_E2E", os.getenv("SKIP_SELENIUM", "")).lower() in ("1", "true", "yes"):
        skip = pytest.mark.skip(reason="SKIP_E2E=1")
        for item in items:
            if "e2e" in item.keywords:
                item.add_marker(skip)
