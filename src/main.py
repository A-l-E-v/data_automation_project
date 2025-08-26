from __future__ import annotations

import argparse
import json

from src.pipelines.runner import run
from src.utils.logging import setup_logging
from src.utils.config import load_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="config/config.yaml")
    args = parser.parse_args()

    setup_logging()

    # Загружаем YAML в dict
    cfg = load_config(args.config)

    result = run(cfg)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
