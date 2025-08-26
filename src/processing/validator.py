from __future__ import annotations

from typing import Dict, List
import numpy as np
import pandas as pd

__all__ = [
    "check_duplicates",
    "drop_duplicates",
    "check_missing",
    "check_types",
    "detect_outliers_iqr",
    "detect_outliers_zscore",
]


def check_duplicates(df: pd.DataFrame) -> int:
    """
    Возвращает число дублей по наихудшей колонке:
      для каждой колонки считаем sum(max(count(v)-1, 0)), затем берём max.
    """
    if df is None or df.empty:
        return 0
    dup_counts = []
    for c in df.columns:
        vc = df[c].value_counts(dropna=True)
        dup_counts.append(int((vc[vc > 1] - 1).sum()))
    return int(max(dup_counts) if dup_counts else 0)


def drop_duplicates(df: pd.DataFrame, subset: List[str] | None = None) -> pd.DataFrame:
    """Удаляет дубликаты строк (по subset или по всем колонкам)."""
    return df.drop_duplicates(subset=subset)


def check_missing(df: pd.DataFrame) -> Dict[str, int]:
    """Количество пропусков по колонкам."""
    return {c: int(df[c].isna().sum()) for c in df.columns}


def check_types(df: pd.DataFrame) -> Dict[str, str]:
    """Типы колонок в текстовом виде."""
    return {c: str(dt) for c, dt in df.dtypes.items()}


def detect_outliers_iqr(
    df: pd.DataFrame, columns: List[str], k: float = 1.5
) -> pd.DataFrame:
    """
    IQR-выбросы: x < Q1 - k*IQR или x > Q3 + k*IQR.
    Возвращает DataFrame из булевых масок по указанным колонкам.
    """
    out = pd.DataFrame(index=df.index)
    for c in columns or []:
        if c not in df.columns:
            continue
        s = pd.to_numeric(df[c], errors="coerce")
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        low = q1 - k * iqr
        high = q3 + k * iqr
        out[c] = (s < low) | (s > high)
    return out


def detect_outliers_zscore(
    df: pd.DataFrame, columns: List[str], threshold: float = 3.0
) -> pd.DataFrame:
    """
    Робастный Z-score: |(x - mean)/std| > threshold.
    std берём по центральной части данных (между Q1 и Q3), чтобы выбросы не раздували дисперсию;
    если такой std некорректен (0/NaN) — используем общий std.
    """
    out = pd.DataFrame(index=df.index)
    for c in columns or []:
        if c not in df.columns:
            continue
        s = pd.to_numeric(df[c], errors="coerce")

        # центральная часть
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        central = s[(s >= q1) & (s <= q3)]
        mu = central.mean() if central.notna().any() else s.mean()
        sd = central.std(ddof=0) if central.notna().any() else s.std(ddof=0)

        if sd == 0 or np.isnan(sd):
            out[c] = False
        else:
            z = (s - mu) / sd
            out[c] = z.abs() > threshold
    return out
