from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from utils.config_loader import project_root


def load_test_data_yaml() -> dict[str, Any]:
    path: Path = project_root() / "data" / "test_data.yaml"
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError("test_data.yaml must be a mapping at root.")
    return data
