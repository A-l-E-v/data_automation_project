from __future__ import annotations

from typing import List, Optional
import pandas as pd
import numpy as np

try:
    from sklearn.preprocessing import StandardScaler, MinMaxScaler

    _SK_OK = True
except Exception:
    _SK_OK = False


__all__ = [
    "impute_missing",
    "encode_categorical",
    "scale_numeric",
    "parse_dates",
]


def impute_missing(
    df: pd.DataFrame,
    strategy: str = "median",
    cat_strategy: str = "most_frequent",
) -> pd.DataFrame:
    """
    Заполняет пропуски:
      - числовые: mean/median (по strategy)
      - категориальные/строки: most_frequent
    """
    out = df.copy()
    num_cols = out.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = [c for c in out.columns if c not in num_cols]

    # numeric
    if num_cols:
        if strategy == "mean":
            fills = out[num_cols].mean(numeric_only=True)
        else:
            fills = out[num_cols].median(numeric_only=True)
        out[num_cols] = out[num_cols].fillna(fills)

    # categorical
    for c in cat_cols:
        mode_val = out[c].mode(dropna=True)
        fill = mode_val.iloc[0] if not mode_val.empty else ""
        out[c] = out[c].fillna(fill)

    return out


def encode_categorical(df: pd.DataFrame, mode: str = "onehot") -> pd.DataFrame:
    """
    Кодирование категориальных:
      - mode="onehot": pandas.get_dummies(drop_first=False)
      - mode="label": codes по .astype('category')

    ВАЖНО: не кодируем потенциальные столбцы-даты/времени (имя содержит "date" или "time"),
    чтобы сохранить исходную колонку под последующий parse_dates().
    """
    out = df.copy()
    # кандидаты в категории
    cat_cols_all = out.select_dtypes(include=["object", "category"]).columns.tolist()
    # исключаем даты/время по имени
    date_like = {
        c for c in cat_cols_all if ("date" in c.lower()) or ("time" in c.lower())
    }
    cat_cols = [c for c in cat_cols_all if c not in date_like]

    if not cat_cols:
        return out

    if mode == "label":
        for c in cat_cols:
            out[c] = out[c].astype("category").cat.codes
        return out

    # onehot
    out = pd.get_dummies(out, columns=cat_cols, prefix=cat_cols, dtype=float)
    return out


def scale_numeric(df: pd.DataFrame, method: str = "standard") -> pd.DataFrame:
    """
    Масштабирование:
      - "standard": среднее ~0, std ~1
      - "minmax": в [0,1]
    """
    out = df.copy()
    num_cols = out.select_dtypes(include=[np.number]).columns.tolist()
    if not num_cols:
        return out

    if method == "minmax":
        if _SK_OK:
            scaler = MinMaxScaler()
            out[num_cols] = scaler.fit_transform(out[num_cols].astype(float))
        else:
            vals = out[num_cols].astype(float)
            out[num_cols] = (vals - vals.min()) / (vals.max() - vals.min()).replace(
                0, 1
            )
        return out

    # standard
    if _SK_OK:
        scaler = StandardScaler(with_mean=True, with_std=True)
        out[num_cols] = scaler.fit_transform(out[num_cols].astype(float))
    else:
        vals = out[num_cols].astype(float)
        out[num_cols] = (vals - vals.mean()) / vals.std(ddof=0).replace(0, 1)
    return out


def parse_dates(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Конвертирует указанные колонки в datetime64[ns]."""
    out = df.copy()
    for c in columns or []:
        if c in out.columns:
            out[c] = pd.to_datetime(out[c], errors="coerce")
    return out
