from __future__ import annotations

from typing import Dict, Iterable, Optional

import pandas as pd


def _select(df: pd.DataFrame, keep: Optional[Iterable[str]]) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    if not keep:
        return df
    cols = [c for c in keep if c in df.columns]
    return df[cols] if cols else df


def build_report_df(
    df_sales: Optional[pd.DataFrame] = None,
    df_users: Optional[pd.DataFrame] = None,
    df_products: Optional[pd.DataFrame] = None,
    keep_columns_cfg: Optional[Dict[str, Iterable[str]]] = None,
) -> pd.DataFrame:
    """
    Сборка единого датафрейма отчёта.
    keep_columns_cfg — словарь вида:
      {
        "sales": ["order_id", "amount", ...],
        "users": ["id", "age", ...],
        "products": ["id", "price", ...]
      }
    Все аргументы — ИМЕНОВАННЫЕ (чтобы не было путаницы и ошибок truth-value).
    """
    keep_columns_cfg = keep_columns_cfg or {}

    parts = []
    if df_sales is not None and not df_sales.empty:
        parts.append(_select(df_sales, keep_columns_cfg.get("sales")))
    if df_users is not None and not df_users.empty:
        parts.append(_select(df_users, keep_columns_cfg.get("users")))
    if df_products is not None and not df_products.empty:
        parts.append(_select(df_products, keep_columns_cfg.get("products")))

    if not parts:
        return pd.DataFrame()

    # просто конкат по колонкам для отчёта-«сводки»; специфические джоины можно будет добавить позже
    return pd.concat(parts, axis=1)
