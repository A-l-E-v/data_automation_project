from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from src.utils.logging import getLogger

log = getLogger(__name__)

ID_COLUMNS = {"order_id", "customer_id"}


def aggregates_by_source(df_sales: pd.DataFrame) -> pd.DataFrame:
    if "source" not in df_sales.columns or df_sales.empty:
        return pd.DataFrame(columns=["source", "rows", "amount_sum", "amount_mean"])
    res = []
    for src, part in df_sales.groupby("source"):
        rows = len(part)
        if "amount" in part.columns:
            amount_sum = float(part["amount"].dropna().astype(float).sum())
            amount_mean = float(part["amount"].dropna().astype(float).mean())
        else:
            amount_sum = np.nan
            amount_mean = np.nan
        res.append(
            {
                "source": src,
                "rows": rows,
                "amount_sum": amount_sum,
                "amount_mean": amount_mean,
            }
        )
    return pd.DataFrame(res)


def overall_metrics(df_raw: pd.DataFrame, df_clean: pd.DataFrame) -> pd.DataFrame:
    rows_raw = len(df_raw)
    rows_clean = len(df_clean)
    dups = rows_raw - len(df_raw.drop_duplicates()) if rows_raw else 0
    miss_amount = (
        int(df_clean["amount"].isna().sum()) if "amount" in df_clean.columns else 0
    )
    total_rev = (
        float(df_clean["amount"].dropna().astype(float).sum())
        if "amount" in df_clean.columns
        else np.nan
    )
    avg_rev = (
        float(df_clean["amount"].dropna().astype(float).mean())
        if "amount" in df_clean.columns
        else np.nan
    )
    return pd.DataFrame(
        [
            {
                "rows_raw": rows_raw,
                "rows_clean": rows_clean,
                "duplicates_raw": int(dups),
                "missing_amount_clean": miss_amount,
                "total_revenue_clean": total_rev,
                "avg_order_amount_clean": avg_rev,
            }
        ]
    )


def _safe_ts_for_decompose(
    df: pd.DataFrame, date_col: str, value_col: str
) -> pd.DataFrame:
    if date_col not in df.columns or value_col not in df.columns:
        return pd.DataFrame()
    sdate = pd.to_datetime(df[date_col], errors="coerce")
    ok = sdate.notna() & df[value_col].notna()
    if not ok.any():
        return pd.DataFrame()
    ser = (
        df.loc[ok, value_col]
        .astype(float)
        .groupby(sdate[ok].dt.floor("D"))
        .sum()
        .sort_index()
    )
    ts = ser.asfreq("D", fill_value=0.0)
    return pd.DataFrame({date_col: ts.index, value_col: ts.values})


# Надёжные импорты basic-аналитики (повторяем логику исходника)
try:
    from src.analysis.basic import basic_stats, decompose_ts
except Exception:
    try:
        from src.basic import basic_stats, decompose_ts  # type: ignore
    except Exception:
        from basic import basic_stats, decompose_ts  # type: ignore


def basic_stats_table(
    df: pd.DataFrame, title_prefix: str = ""
) -> tuple[str, list[list[str]]]:
    work = df.drop(
        columns=[c for c in df.columns if c in ID_COLUMNS], errors="ignore"
    ).select_dtypes(include=[np.number])
    if work.empty:
        return (f"{title_prefix}Числовые сводки (нет данных)", [["нет данных"]])
    desc = work.describe().T
    desc.index.name = "Колонка"
    order = ["count", "mean", "std", "min", "25%", "50%", "75%", "max"]
    cols = [c for c in order if c in desc.columns] + [
        c for c in desc.columns if c not in order
    ]
    desc = desc[cols]
    header = [desc.index.name] + [str(c) for c in desc.columns]
    rows = [header]
    for idx, row in desc.iterrows():
        rows.append(
            [str(idx)]
            + [
                f"{v:.4g}" if isinstance(v, (int, float, np.floating)) else str(v)
                for v in row.tolist()
            ]
        )
    return (f"{title_prefix}Числовые сводки (basic_stats)", rows)


def build_pdf_tables(df_clean: pd.DataFrame) -> list[tuple[str, list[list[str]]]]:
    tables: list[tuple[str, list[list[str]]]] = []
    tables.append(basic_stats_table(df_clean))
    if "source" in df_clean.columns and not df_clean.empty:
        for src_name, part in df_clean.groupby("source"):
            tables.append(
                basic_stats_table(part, title_prefix=f"Источник {src_name}: ")
            )
    try:
        safe_df = _safe_ts_for_decompose(df_clean, "order_date", "amount")
        if not safe_df.empty:
            dec = decompose_ts(safe_df, "order_date", "amount", freq="D") or {}
            if any(float(v) != 0.0 for v in dec.values()):
                header = ["Показатель", "Значение"]
                rows = [header] + [[str(k), str(v)] for k, v in dec.items()]
                tables.append(("Декомпозиция временного ряда (по дням)", rows))
    except Exception as e:
        log.info("decompose_ts: ошибка подготовки таблицы: %s", e)
    return tables
