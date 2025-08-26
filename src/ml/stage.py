from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd
from src.utils.logging import getLogger
from .utils import ensure_dir
from .features import build_features
from .classification import run_classification
from .regression import run_regression

log = getLogger(__name__)


def run_ml(df_cleaned: pd.DataFrame, cfg: Dict[str, Any]) -> Dict[str, Any]:
    ml_cfg = cfg.get("ml") or {}
    if not ml_cfg or not bool(ml_cfg.get("enabled", True)):
        log.info("ML отключён — пропускаем.")
        return {
            "metrics": {},
            "images": [],
            "models": {},
            "tables": [],
            "tables_df": {},
        }

    out_dir = (
        Path(
            cfg.get("reporting", {})
            .get("plots", {})
            .get("output_dir", "reports/images")
        )
        / "ml"
    )
    models_dir = Path(ml_cfg.get("models_dir", "models"))
    ensure_dir(out_dir)
    ensure_dir(models_dir)

    X = build_features(df_cleaned)
    images: List[Tuple[str, str]] = []
    metrics: Dict[str, Any] = {"classification": {}, "regression": {}}
    tables: List[Tuple[str, List[List[str]]]] = []
    tables_df: Dict[str, Any] = {}

    run_classification(
        X, ml_cfg, out_dir, models_dir, images, tables, tables_df, metrics
    )
    run_regression(X, ml_cfg, out_dir, models_dir, images, tables, tables_df, metrics)

    return {
        "metrics": metrics,
        "images": images,
        "models": {},
        "tables": tables,
        "tables_df": tables_df,
    }
