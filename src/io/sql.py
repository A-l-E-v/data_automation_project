from __future__ import annotations

from typing import Dict, Tuple
import os
import pandas as pd
from sqlalchemy import create_engine

from src.utils.logging import getLogger

logger = getLogger(__name__)


def _shorten(sql: str, n: int = 120) -> str:
    s = " ".join((sql or "").strip().split())
    return s if len(s) <= n else s[: n - 3] + "..."


def read_sql_source(cfg_sql: Dict) -> Tuple[pd.DataFrame, str]:
    """
    Загружает данные из PostgreSQL по DSN и SQL-запросу (включая сложные с JOIN/агрегатами).
    Возвращает (DataFrame, исходный SQL для отчётов/логов).

    Поддерживает:
      - cfg_sql["dsn"]      — DSN строка
      - cfg_sql["env_dsn"]  — имя переменной окружения с DSN
      - cfg_sql["query"]    — SQL-запрос
    """
    dsn = cfg_sql.get("dsn") or os.getenv(str(cfg_sql.get("env_dsn") or ""), "")
    query = (cfg_sql.get("query") or "").strip()

    if not dsn or not query:
        logger.info("SQL-источник пропущен: dsn или query не заданы.")
        return pd.DataFrame(), query

    try:
        engine = create_engine(dsn)
        with engine.connect() as conn:
            df = pd.read_sql_query(query, conn)
        logger.info("SQL loaded: shape=%s; query=%s", df.shape, _shorten(query))
        return df, query
    except Exception as e:
        logger.exception("Ошибка при загрузке SQL: %s", e)
        return pd.DataFrame(), query
