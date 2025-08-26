"""Базовые статистики и анализ временных рядов."""

from __future__ import annotations
from typing import Dict, Any
import pandas as pd
import numpy as np
from statsmodels.tsa.seasonal import seasonal_decompose


def basic_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Основные статистики по числовым столбцам."""
    desc = df.describe(include=[np.number]).to_dict()
    return {k: {kk: float(vv) for kk, vv in v.items()} for k, v in desc.items()}


def decompose_ts(
    df: pd.DataFrame, date_col: str, target_col: str, freq: str = "D"
) -> Dict[str, Any]:
    """Декомпозиция: тренд, сезонность, остаток. Возвращает агрегаты (без графиков)."""
    ts = df[[date_col, target_col]].dropna().copy()
    ts = ts.sort_values(date_col)
    ts = ts.set_index(date_col).asfreq(freq)
    result = seasonal_decompose(
        ts[target_col], model="additive", period=None, extrapolate_trend="freq"
    )
    return {
        "trend_nan": int(result.trend.isna().sum() if result.trend is not None else 0),
        "seasonal_nan": int(
            result.seasonal.isna().sum() if result.seasonal is not None else 0
        ),
        "resid_nan": int(result.resid.isna().sum() if result.resid is not None else 0),
    }
