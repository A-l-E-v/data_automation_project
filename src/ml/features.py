from __future__ import annotations
import pandas as pd
import numpy as np
from .utils import ID_COLUMNS


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    if "order_date" in x.columns:
        s = pd.to_datetime(x["order_date"], errors="coerce")
        x["dow"] = s.dt.dayofweek
        x["month"] = s.dt.month
        x["is_weekend"] = (x["dow"] >= 5).astype("Int64")
    if "source" in x.columns:
        x = pd.get_dummies(x, columns=["source"], prefix="src", dummy_na=False)
    if "customer_id" in x.columns:
        x["_cnt_prev"] = x.groupby("customer_id").cumcount()
        if "amount" in x.columns:
            x["_amount_prev_mean"] = x.groupby("customer_id")["amount"].transform(
                lambda s: s.shift().expanding().mean()
            )
    for c in ["_cnt_prev", "_amount_prev_mean", "dow", "month", "is_weekend"]:
        if c in x.columns:
            x[c] = x[c].fillna(0)
    x = x.drop(columns=[c for c in ["order_id"] if c in x.columns], errors="ignore")
    return x


def make_classification_target(df: pd.DataFrame, target: str | None, q: float):
    if target and target in df.columns:
        return df[target].astype(int), target
    if "amount" not in df.columns:
        raise ValueError("No 'amount' column to derive classification target.")
    thr = df["amount"].dropna().astype(float).quantile(q)
    y = (df["amount"].astype(float) >= thr).astype(int)
    return y, f"high_value_q{q:.2f}"


def select_numeric_features(X: pd.DataFrame, drop: list[str]):
    feat = (
        X.drop(columns=drop, errors="ignore")
        .select_dtypes(include=[np.number])
        .fillna(0.0)
    )
    feat = feat.drop(
        columns=[c for c in feat.columns if c in ID_COLUMNS], errors="ignore"
    )
    return feat, feat.columns.tolist()
