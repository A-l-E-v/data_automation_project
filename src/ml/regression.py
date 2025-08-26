from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from src.utils.persist import save_model
from src.utils.logging import getLogger
from .features import select_numeric_features
from .plots import reg_scatter, residuals, bar
from .tables import rf_importance_table

log = getLogger(__name__)


def run_regression(
    X: pd.DataFrame,
    ml_cfg: Dict[str, Any],
    out_dir: Path,
    models_dir: Path,
    images: List[Tuple[str, str]],
    tables,
    tables_df,
    metrics_dest: Dict[str, Any],
):
    cfg = ml_cfg.get("regression", {})
    if not bool(cfg.get("enabled", True)) or ("amount" not in X.columns):
        return
    try:
        y = X["amount"].astype(float)
        feat, feat_cols = select_numeric_features(X, drop=["amount"])  # drop target
        mask = y.notna()
        y = y.loc[mask]
        feat = feat.loc[mask]
        log.info("Регрессия: признаков=%d", feat.shape[1])
        Xtr, Xte, ytr, yte = train_test_split(feat, y, test_size=0.25, random_state=42)
        reg = RandomForestRegressor(n_estimators=250, random_state=42)
        reg.fit(Xtr, ytr)
        pred = reg.predict(Xte)
        mse = float(mean_squared_error(yte, pred))
        m = {
            "rmse": float(np.sqrt(mse)),
            "mae": float(mean_absolute_error(yte, pred)),
            "r2": float(r2_score(yte, pred)),
            "n_train": int(len(Xtr)),
            "n_test": int(len(Xte)),
        }
        metrics_dest["regression"] = m
        log.info("ML[regression] %s", m)
        images.append(
            (
                reg_scatter(yte.values, pred, out_dir / "reg_scatter.png"),
                "Скаттер факт–прогноз.",
            )
        )
        images.append(
            (
                residuals(yte.values, pred, out_dir / "reg_residuals.png"),
                "Распределение остатков.",
            )
        )
        title, rows, dfi = rf_importance_table(reg, feat_cols, top_k=20)
        tables.append((title, rows))
        tables_df["rf_importance"] = dfi
        if not dfi.empty:
            top = dfi.sort_values("importance", ascending=False).head(20)
            img = bar(
                top["feature"].tolist(),
                top["importance"].tolist(),
                "RandomForest: важности (топ-20)",
                out_dir / "reg_feature_importance.png",
            )
            images.append((img, "Важности признаков RF."))
        model_path = models_dir / "rf_amount.joblib"
        save_model(reg, model_path)
    except Exception as e:
        log.exception("Ошибка регрессии: %s", e)
