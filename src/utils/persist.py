"""Сохранение результатов в БД (PostgreSQL) и на диск."""

from __future__ import annotations
from typing import Optional
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine


def save_df_to_db(
    df: pd.DataFrame, conn_str: str, table: str, if_exists: str = "append"
) -> None:
    engine = create_engine(conn_str, future=True)
    with engine.begin() as conn:
        df.to_sql(table, con=conn, if_exists=if_exists, index=False)


def save_model(model, path: str | Path) -> None:
    import joblib

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
