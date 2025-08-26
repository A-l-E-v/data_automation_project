from __future__ import annotations

from typing import Dict, Tuple
import pandas as pd
import numpy as np

from src.utils.logging import getLogger

log = getLogger(__name__)


def _drop_high_missing_columns(
    df: pd.DataFrame, threshold: float
) -> tuple[pd.DataFrame, list[str]]:
    """
    Удаляет колонки, где доля пропусков > threshold (0..1).
    Возвращает (df2, dropped_cols)
    """
    if df.empty:
        return df, []
    na_ratio = df.isna().mean()
    to_drop = [c for c, r in na_ratio.items() if r > threshold]
    df2 = df.drop(columns=to_drop) if to_drop else df
    return df2, to_drop


def _coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    """Аккуратно приводим типы, не падаем на ошибках."""
    out = df.copy()
    if "order_id" in out.columns:
        out["order_id"] = pd.to_numeric(out["order_id"], errors="coerce").astype(
            "Int64"
        )
    if "customer_id" in out.columns:
        out["customer_id"] = pd.to_numeric(out["customer_id"], errors="coerce").astype(
            "Int64"
        )
    if "amount" in out.columns:
        out["amount"] = pd.to_numeric(out["amount"], errors="coerce")
    if "order_date" in out.columns:
        out["order_date"] = pd.to_datetime(out["order_date"], errors="coerce")
    return out


def run_cleaning(df_sales: pd.DataFrame, cfg: Dict) -> Tuple[pd.DataFrame, Dict]:
    """
    Мини-очистка витрины продаж:
      - приведение типов
      - удаление столбцов с высокой долей пропусков (threshold из конфига)
      - базовые метрики для логов/отчётов
    Возвращает (df_cleaned, stats_dict)
    """
    cleaner_cfg = (cfg.get("processing", {}) or {}).get("cleaner", {}) or {}
    thr = float(
        ((cleaner_cfg.get("drop_high_missing_columns", {}) or {}).get("threshold", 0.8))
    )

    # 1) типы
    df = _coerce_types(df_sales)

    # 2) удалим колонки с высокой долей NaN (логируем)
    df2, dropped = _drop_high_missing_columns(df, thr)
    if dropped:
        log.info(
            "drop_high_missing_columns: dropped %d columns: %s",
            len(dropped),
            ", ".join(dropped),
        )
    else:
        log.info("drop_high_missing_columns: ничего не удалено (threshold=%.2f)", thr)

    # 3) базовые метрики
    #   - дубликаты строк (по всем колонкам)
    sales_duplicates = int(len(df2) - len(df2.drop_duplicates()))
    #   - пропуски по ключевым колонкам (если они есть)
    key_cols = ["order_id", "customer_id", "order_date", "amount", "country"]
    sales_missing = {}
    for c in key_cols:
        if c in df2.columns:
            sales_missing[c] = int(df2[c].isna().sum())

    stats = {
        "sales_duplicates": sales_duplicates,
        "sales_missing": sales_missing,
    }

    return df2, stats
