from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping, Optional

import yaml


class Config(dict):
    """
    Обёртка над dict:
      - доступ к ключам как к атрибутам (cfg.foo)
      - .base_dir, .path (метаданные)
      - безопасный доступ к отсутствующим атрибутам:
          * для некоторых ожидаемых узлов (settings) -> {}
          * прочие -> None
      - синтетические удобные поля:
          * .data_processed -> <base_dir>/data/processed (или "data/processed")
    """

    _SAFE_EMPTY_DICT_KEYS = {
        "settings"
    }  # <-- узлы, которые возвращаем как {} если их нет

    def __init__(
        self,
        data: Mapping[str, Any] | None = None,
        *,
        base_dir: Optional[Path] = None,
        path: Optional[Path] = None,
    ):
        super().__init__(data or {})
        object.__setattr__(self, "_base_dir", str(base_dir) if base_dir else None)
        object.__setattr__(self, "_path", str(path) if path else None)

    def __getattr__(self, item: str) -> Any:
        # служебные
        if item == "base_dir":
            return object.__getattribute__(self, "_base_dir")
        if item == "path":
            return object.__getattribute__(self, "_path")

        # прямое соответствие ключам
        if item in self.keys():
            return self[item]

        # безопасные пустые словари для ожидаемых узлов
        if item in self._SAFE_EMPTY_DICT_KEYS:
            return {}

        # синтетическое поле
        if item == "data_processed":
            bd = object.__getattribute__(self, "_base_dir")
            return str(Path(bd) / "data" / "processed") if bd else "data/processed"

        # по умолчанию — None
        return None

    def __setattr__(self, key: str, value: Any) -> None:
        if key in {"_base_dir", "_path"}:
            object.__setattr__(self, key, value)
        elif key in {"base_dir", "path"}:
            object.__setattr__(self, f"_{key}", value)
        else:
            self[key] = value

    def to_dict(self) -> Dict[str, Any]:
        d = dict(self)
        d["_meta"] = {"base_dir": self.base_dir, "path": self.path}
        return d


def load_config(path: str | Path) -> Config:
    """
    Загружает YAML и возвращает Config:
      - dict-совместимо (cfg.get(...))
      - атрибутный доступ (cfg.foo)
      - .base_dir / .path
      - .settings -> {} если отсутствует
      - .data_processed -> путь по умолчанию
    """
    p = Path(path).resolve()
    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    # предполагаем <project_root>/config/config.yaml → base_dir = <project_root>
    base_dir = p.parent.parent if p.name.endswith(".yaml") else p.parent
    return Config(data, base_dir=base_dir, path=p)
