"""
Совместимость с тестами: tests/test_pipeline.py вызывает run(Path).
Здесь загружаем YAML сами и прокидываем dict в runner.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from src.pipelines.runner import run as run_pipeline_dict
from src.utils.config import load_config


def run(config_path_or_dict: str | Path | Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(config_path_or_dict, (str, Path)):
        cfg = load_config(config_path_or_dict)
    else:
        cfg = dict(config_path_or_dict or {})
    return run_pipeline_dict(cfg)
