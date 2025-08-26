from __future__ import annotations
from typing import Dict
import json
from pathlib import Path

import pandas as pd

from src.utils.logging import getLogger
from src.pipelines.io_stage import load_sources
from src.pipelines.clean_stage import run_cleaning
from src.pipelines.ml_stage import run_ml
from src.pipelines.report_stage import run_reporting
from src.pipelines.email_stage import send_email_with_artifacts

logger = getLogger(__name__)


def run_pipeline(cfg: Dict) -> Dict:
    logger.info("Старт конвейера")

    # 1) Источники
    df_sales, df_users, df_products = load_sources(cfg)
    logger.info(
        "Concat all -> shapes: sales=%s users=%s products=%s",
        df_sales.shape,
        df_users.shape,
        df_products.shape,
    )

    # Диапазон дат, валюта, распределение по источникам
    currency = cfg.get("reporting", {}).get("units", {}).get("currency_label", "у.е.")
    if "order_date" in df_sales.columns:
        _d = pd.to_datetime(df_sales["order_date"], errors="coerce")
        dmin, dmax = _d.min(), _d.max()
        logger.info("Диапазон дат: %s — %s; валюта: %s", dmin, dmax, currency)
    if "source" in df_sales.columns:
        counts = df_sales["source"].value_counts(dropna=False).to_dict()
        logger.info("Распределение строк по источникам: %s", counts)

    # 2) Очистка
    df_raw = df_sales.copy()
    df_cleaned, clean_stats = run_cleaning(df_sales, cfg)
    logger.info("Очистка готова: stats=%s", clean_stats)

    # 3) ML
    ml_result = run_ml(df_cleaned, cfg)
    ml_metrics = ml_result.get("metrics", {})
    ml_images = ml_result.get("images", [])
    models_saved = ml_result.get("models", {})
    ml_tables = ml_result.get("tables", [])
    ml_tables_df = ml_result.get("tables_df", {})

    if ml_metrics:
        logger.info("ML метрики: %s", ml_metrics)
    if models_saved:
        logger.info("Сохранённые модели: %s", models_saved)

    # 4) Отчёты (включая ML-картинки и таблицы)
    artifacts = run_reporting(
        df_raw,
        df_cleaned,
        cfg,
        extra_images_with_captions=ml_images,
        extra_tables=ml_tables,
        extra_tables_df=ml_tables_df,
    )

    # 5) Email
    try:
        email_cfg = cfg.get("email", {}) or {}
        if email_cfg.get("enabled", False):
            send_email_with_artifacts(email_cfg, artifacts)
            logger.info("email: письмо отправлено")
    except Exception as e:
        logger.exception("Ошибка при отправке письма: %s", e)

    summary = {
        "raw": str(
            Path(
                cfg.get("artifacts", {})
                .get("paths", {})
                .get("raw", "data/processed/_combined_raw.parquet")
            )
        ),
        "cleaned": str(
            Path(
                cfg.get("artifacts", {})
                .get("paths", {})
                .get("cleaned", "data/processed/cleaned.parquet")
            )
        ),
        "stats": clean_stats,
        "ml_metrics": ml_metrics,
        "models": models_saved,
        "artifacts": artifacts,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    logger.info("Конвейер завершён")
    return summary


def run(cfg: Dict) -> Dict:
    return run_pipeline(cfg)
