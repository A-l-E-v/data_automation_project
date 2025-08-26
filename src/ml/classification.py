from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)
from src.utils.persist import save_model
from src.utils.logging import getLogger
from .features import make_classification_target, select_numeric_features
from .plots import (
    confusion as plot_confusion,
    roc as plot_roc,
    pr as plot_pr,
    bar as plot_bar,
)
from .tables import logreg_coeffs_table

log = getLogger(__name__)


def run_classification(
    X,
    ml_cfg: Dict[str, Any],
    out_dir: Path,
    models_dir: Path,
    images: List[Tuple[str, str]],
    tables,
    tables_df,
    metrics_dest: Dict[str, Any],
):
    cfg = ml_cfg.get("classification", {})
    if not bool(cfg.get("enabled", True)):
        return
    try:
        q = float(cfg.get("threshold_q", 0.8))
        y, y_name = make_classification_target(X, cfg.get("target"), q)
        feat, feat_cols = select_numeric_features(
            X, drop=[y_name, "amount"]
        )  # drop target & amount
        Xtr, Xte, ytr, yte = train_test_split(
            feat, y, test_size=0.25, random_state=42, stratify=y
        )
        clf = LogisticRegression(max_iter=1000, class_weight="balanced")
        clf.fit(Xtr, ytr)
        proba = clf.predict_proba(Xte)[:, 1]
        pred = (proba >= 0.5).astype(int)
        m = {
            "target": y_name,
            "accuracy": float(accuracy_score(yte, pred)),
            "precision": float(precision_score(yte, pred, zero_division=0)),
            "recall": float(recall_score(yte, pred, zero_division=0)),
            "f1": float(f1_score(yte, pred, zero_division=0)),
            "roc_auc": float(roc_auc_score(yte, proba)),
            "n_train": int(len(Xtr)),
            "n_test": int(len(Xte)),
        }
        metrics_dest["classification"] = m
        log.info("ML[classification] %s", m)
        cm = confusion_matrix(yte, pred)
        images.append(
            (
                plot_confusion(cm, out_dir / "clf_confusion.png"),
                "Матрица ошибок: диагональ — верные ответы.",
            )
        )
        images.append(
            (
                plot_roc(yte.values, proba, out_dir / "clf_roc.png"),
                "ROC-кривая; ROC-AUC — качество ранжирования.",
            )
        )
        images.append(
            (
                plot_pr(yte.values, proba, out_dir / "clf_pr.png"),
                "Precision–Recall кривая.",
            )
        )
        title, rows, dfc = logreg_coeffs_table(clf, feat_cols, top_k=20)
        tables.append((title, rows))
        tables_df["logreg_coeffs"] = dfc
        if not dfc.empty:
            top = dfc.head(20)
            img = plot_bar(
                top["feature"].tolist(),
                top["abs_coef"].tolist(),
                "LogReg: топ-20 |коэфф|",
                out_dir / "clf_top_coef.png",
            )
            images.append((img, "Наиболее влияющие признаки по |коэф|."))
        model_path = models_dir / "logreg_high_value.joblib"
        save_model(clf, model_path)
    except Exception as e:
        log.exception("Ошибка классификации: %s", e)
