from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

from src.io.loader import load_csv, load_excel, call_api
from src.io.sql import read_sql_source
from src.utils.logging import getLogger

logger = getLogger(__name__)


def _safe_load_csv(path: str | Path) -> pd.DataFrame:
    try:
        logger.info("Загрузка CSV: %s", path)
        return load_csv(str(path))
    except Exception as e:
        logger.warning("CSV пропущен (%s): %s", path, e)
        return pd.DataFrame()


def _safe_load_excel(path: str | Path, sheet: str | int | None) -> pd.DataFrame:
    try:
        logger.info("Загрузка Excel: %s:%s", path, sheet if sheet is not None else "")
        return load_excel(str(path), sheet if sheet is not None else 0)
    except Exception as e:
        logger.warning("Excel пропущен (%s): %s", path, e)
        return pd.DataFrame()


def _safe_call_api(ep: Dict) -> pd.DataFrame:
    try:
        url = ep.get("url", "")
        logger.info(
            "Вызов API: %s method=%s json_root=%s paginate=%s",
            url,
            ep.get("method", "GET"),
            ep.get("json_root", None),
            bool(ep.get("paginate")),
        )
        return call_api(ep)
    except Exception as e:
        logger.error("Ошибка при вызове API: %s (%s)", ep, e)
        return pd.DataFrame()


def _safe_read_sql(item: Dict) -> pd.DataFrame:
    df, query = read_sql_source(item)
    name = str(item.get("name", "")).lower()
    if df.empty:
        logger.warning(
            "SQL источник пуст или не загружен: name=%s; query=%s",
            name,
            (query or "").strip(),
        )
    else:
        logger.info("Загружено из SQL: %s rows=%d", name, len(df))
    return df


def _add_source(df: pd.DataFrame, source: str) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    out = df.copy()
    out["source"] = (
        source if "source" not in out.columns else out["source"].fillna(source)
    )
    return out


def _classify_target(
    name: str, df: pd.DataFrame, explicit_target: str | None
) -> str | None:
    if explicit_target:
        return explicit_target.lower()
    low = name.lower()
    if low in ("sales", "orders"):
        return "sales"
    if low in ("users", "user"):
        return "users"
    if low in ("products", "product"):
        return "products"
    if low in ("customers", "clients", "customer"):
        return "customers"

    cols = set(c.lower() for c in df.columns)
    if {"order_id", "amount"} <= cols:
        return "sales"
    if {"customer_id", "country"} <= cols:
        return "customers"
    if {"id", "firstname", "email"} <= cols:
        return "users"
    if {"id", "title", "price"} <= cols:
        return "products"
    return None


def load_sources(cfg: Dict) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    sources = cfg.get("sources", {}) or {}

    sales_parts: List[pd.DataFrame] = []
    users_df = pd.DataFrame()
    products_df = pd.DataFrame()

    # SQL
    for item in sources.get("sql", []) or []:
        name = str(item.get("name", "")).lower()
        target = str(item.get("target", "")).lower() or None
        df = _safe_read_sql(item)
        if df.empty:
            continue
        dst = _classify_target(name, df, target)
        if dst in ("sales", "customers"):
            sales_parts.append(_add_source(df, "db"))
        elif dst == "users":
            users_df = _add_source(df, "db")
        elif dst == "products":
            products_df = _add_source(df, "db")
        else:
            sales_parts.append(_add_source(df, "db"))
            logger.info(
                "SQL '%s' без явного target — помещён в sales по умолчанию", name
            )

    # CSV
    for item in sources.get("csv", []) or []:
        name = str(item.get("name", "")).lower()
        path = item.get("path")
        if not path:
            continue
        df = _safe_load_csv(path)
        if df.empty:
            continue
        dst = _classify_target(name, df, item.get("target"))
        if dst in ("sales", "customers"):
            sales_parts.append(_add_source(df, "file"))
        elif dst == "users":
            users_df = _add_source(df, "file")
        elif dst == "products":
            products_df = _add_source(df, "file")

    # Excel
    for item in sources.get("excel", []) or []:
        name = str(item.get("name", "")).lower()
        path = item.get("path")
        sheet = item.get("sheet") or item.get("sheet_name")
        if not path:
            continue
        df = _safe_load_excel(path, sheet)
        if df.empty:
            continue
        dst = _classify_target(name, df, item.get("target"))
        if dst in ("sales", "customers"):
            sales_parts.append(_add_source(df, "file"))
        elif dst == "users":
            users_df = _add_source(df, "file")
        elif dst == "products":
            products_df = _add_source(df, "file")

    # API
    for ep in sources.get("api", []) or []:
        name = str(ep.get("name", "")).lower()
        df = _safe_call_api(ep)
        if df.empty:
            continue
        dst = _classify_target(name, df, ep.get("target"))
        if dst in ("sales", "customers") or ("sale" in name or "order" in name):
            sales_parts.append(_add_source(df, "api"))
        elif dst == "users" or "user" in name:
            users_df = _add_source(df, "api")
        elif dst == "products" or "product" in name:
            products_df = _add_source(df, "api")

    # fallback
    if not sales_parts:
        for pth in ("data/raw/sales.csv", "data/raw/customers.csv"):
            if Path(pth).exists():
                df = _safe_load_csv(pth)
                if not df.empty:
                    sales_parts.append(_add_source(df, "file"))
        xls = Path("data/raw/sales.xlsx")
        if xls.exists():
            sales_parts.append(_add_source(_safe_load_excel(xls, "Sheet1"), "file"))

    df_sales = (
        pd.concat(
            [d for d in sales_parts if d is not None and not d.empty],
            ignore_index=True,
            sort=False,
        )
        if sales_parts
        else pd.DataFrame()
    )

    return df_sales, users_df, products_df
