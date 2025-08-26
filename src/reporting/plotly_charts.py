from __future__ import annotations
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
import plotly.express as px


def monthly_revenue_html(
    df: pd.DataFrame,
    date_col: str,
    amount_col: str,
    out_path: Path | str,
    units: Optional[Dict] = None,
) -> Optional[str]:
    units = units or {
        "currency_label": "у.е.",
        "amount_label": "Выручка",
        "orders_label": "Заказы",
        "date_format": "%Y-%m",
    }
    cur = units.get("currency_label", "у.е.")
    amount_label = units.get("amount_label", "Выручка")

    if date_col not in df.columns or amount_col not in df.columns:
        return None

    d = pd.to_datetime(df[date_col], errors="coerce")
    tmp = df.assign(_d=d).dropna(subset=["_d", amount_col])
    ser = tmp.groupby(tmp["_d"].dt.to_period("M"))[amount_col].sum().sort_index()

    n = len(tmp)
    title = f"{amount_label} по месяцам — период {d.min():%Y-%m}…{d.max():%Y-%m} (N={n}, валюта: {cur})"

    x = ser.index.astype(str)
    fig = px.line(x=x, y=ser.values, markers=True)
    fig.update_traces(
        hovertemplate=f"Месяц=%{{x}}<br>{amount_label}, {cur}=%{{y:.2f}}<extra></extra>"
    )
    fig.update_layout(
        title=title,
        xaxis_title="Месяц",
        yaxis_title=f"{amount_label}, {cur}",
        annotations=[
            dict(
                x=1,
                y=-0.25,
                xref="paper",
                yref="paper",
                showarrow=False,
                text=f"Источник данных: SQL/CSV/Excel/API",
            )
        ],
        margin=dict(t=60, l=50, r=30, b=80),
    )

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(out_path), include_plotlyjs="cdn")
    return str(out_path)


def top_customers_html(
    df: pd.DataFrame,
    customer_col: str,
    out_path: Path | str,
    top_n: int = 10,
    units: Optional[Dict] = None,
) -> Optional[str]:
    units = units or {"orders_label": "Заказы"}
    orders_label = units.get("orders_label", "Заказы")

    if customer_col not in df.columns:
        return None

    top = df.groupby(customer_col).size().sort_values(ascending=False).head(int(top_n))
    n_orders = len(df)
    n_users = df[customer_col].nunique()
    title = f"Топ-{len(top)} клиентов по числу заказов (N={n_orders}, уник. клиентов={n_users})"

    fig = px.bar(x=top.index.astype(str), y=top.values)
    fig.update_traces(
        hovertemplate=f"ID клиента=%{{x}}<br>{orders_label}, шт.=%{{y}}<extra></extra>"
    )
    fig.update_layout(
        title=title,
        xaxis_title="ID клиента (категория)",
        yaxis_title=f"{orders_label}, шт.",
        margin=dict(t=60, l=50, r=30, b=50),
        annotations=[
            dict(
                x=1,
                y=-0.22,
                xref="paper",
                yref="paper",
                showarrow=False,
                text="Примечание: ID — категориальные ключи; метрики по ID не интерпретируются как числа",
            )
        ],
    )

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(out_path), include_plotlyjs="cdn")
    return str(out_path)
