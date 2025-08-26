from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ID_COLUMNS = {"order_id", "customer_id"}


def _units(plots_cfg: Dict, df: pd.DataFrame):
    u = (
        plots_cfg.get("parent_units")
        or plots_cfg.get("units")
        or {
            "currency_label": "у.е.",
            "amount_label": "Выручка",
            "orders_label": "Заказы",
            "date_format": "%Y-%m",
        }
    )
    cur = u.get("currency_label", "у.е.")
    amount_label = u.get("amount_label", "Выручка")
    orders_label = u.get("orders_label", "Заказы")
    date_fmt = u.get("date_format", "%Y-%m")

    dmin = dmax = None
    if "order_date" in df.columns:
        dser = pd.to_datetime(df["order_date"], errors="coerce")
        dmin, dmax = dser.min(), dser.max()
    period_txt = (
        f" — период {dmin:%Y-%m-%d}…{dmax:%Y-%m-%d}"
        if (dmin is not None and dmax is not None)
        else ""
    )
    return cur, amount_label, orders_label, date_fmt, period_txt


def _save(ax, path: Path, title: str, xlabel: str, ylabel: str):
    ax.set_title(title)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3)
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=130)
    plt.close(ax.figure)
    return str(path)


def _sales_hist(df, cfg, outdir, cur, amount_label):
    col = cfg.get("column", "amount")
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(df[col].dropna().astype(float), bins=30)
    p = Path(outdir) / cfg.get("filename", "sales/amount_hist.png")
    title = cfg.get("title_ru", f"Распределение {amount_label.lower()}")
    xlabel = cfg.get("xlabel_ru", f"{amount_label}, {cur}")
    ylabel = cfg.get("ylabel_ru", "Частота, шт.")
    img = _save(ax, p, title, xlabel, ylabel)
    cap = f"Гистограмма {amount_label.lower()}; ось X — {amount_label}, {cur}; ось Y — частота."
    return (img, cap)


def _sales_hist_trim(df, cfg, outdir, cur, amount_label):
    q = float(cfg.get("trim_quantile", 0.99))
    col = cfg.get("column", "amount")
    x = df[col].dropna().astype(float)
    x = x[x <= x.quantile(q)]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(x, bins=30)
    p = Path(outdir) / cfg.get("filename", "sales/amount_hist_trim.png")
    title = cfg.get(
        "title_ru", f"Распределение {amount_label.lower()} (обрезано по q={q:.2f})"
    )
    xlabel = cfg.get("xlabel_ru", f"{amount_label}, {cur}")
    ylabel = cfg.get("ylabel_ru", "Частота, шт.")
    img = _save(ax, p, title, xlabel, ylabel)
    cap = f"Гистограмма {amount_label.lower()} (<= Q{q:.2f}); X — {amount_label}, {cur}; Y — частота."
    return (img, cap)


def _sales_box(df, cfg, outdir, cur, amount_label):
    col = cfg.get("column", "amount")
    fig, ax = plt.subplots(figsize=(6, 4))
    if "source" in df.columns:
        labels = sorted(df["source"].dropna().unique())
        data = [
            df.loc[df["source"] == src, col].dropna().astype(float) for src in labels
        ]
        ax.boxplot(data, labels=labels)
    else:
        ax.boxplot([df[col].dropna().astype(float)])
    p = Path(outdir) / cfg.get("filename", "sales/amount_box.png")
    title = cfg.get("title_ru", f"Боксплот {amount_label.lower()}")
    xlabel = cfg.get("xlabel_ru", "Источник данных")
    ylabel = cfg.get("ylabel_ru", f"{amount_label}, {cur}")
    img = _save(ax, p, title, xlabel, ylabel)
    cap = f"Боксплот по источникам; X — источник; Y — {amount_label}, {cur}."
    return (img, cap)


def _ts_orders(df, cfg, outdir, orders_label, period_txt):
    date_col = cfg.get("date_col", "order_date")
    sdate = pd.to_datetime(df[date_col], errors="coerce")
    ser = sdate.dropna().dt.floor("D").value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(ser.index, ser.values, linewidth=1.3)
    p = Path(outdir) / cfg.get("filename", "sales/orders_over_time.png")
    title = cfg.get("title_ru", f"{orders_label} по дням{period_txt}")
    xlabel = cfg.get("xlabel_ru", "Дата")
    ylabel = cfg.get("ylabel_ru", f"{orders_label}, шт.")
    img = _save(ax, p, title, xlabel, ylabel)
    cap = f"Динамика количества заказов; X — дата; Y — {orders_label}, шт."
    return (img, cap)


def _top_customers(df, cfg, outdir, orders_label, period_txt):
    id_col = cfg.get("id_col", "customer_id")
    top_n = int(cfg.get("top_n", 10))
    top = df.groupby(id_col).size().sort_values(ascending=False).head(top_n)

    # рисуем по числовым позициям — без category-предупреждений
    idx = np.arange(len(top))
    labels = top.index.astype(str).tolist()

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(idx, top.values)
    ax.set_xticks(idx)
    ax.set_xticklabels(labels, rotation=0)

    p = Path(outdir) / cfg.get("filename", "sales/top_customers.png")
    title = cfg.get(
        "title_ru", f"Топ-{len(top)} клиентов по количеству заказов{period_txt}"
    )
    xlabel = cfg.get("xlabel_ru", "ID клиента (категория)")
    ylabel = cfg.get("ylabel_ru", f"{orders_label}, шт.")
    img = _save(ax, p, title, xlabel, ylabel)
    cap = f"Рейтинг клиентов по числу заказов; X — ID клиента (категория); Y — {orders_label}, шт."
    return (img, cap)


def _monthly_revenue(df, cfg, outdir, cur, amount_label):
    date_col = cfg.get("date_col", "order_date")
    amount_col = cfg.get("amount_col", "amount")
    d = pd.to_datetime(df[date_col], errors="coerce")
    tmp = df.assign(_d=d).dropna(subset=["_d", amount_col])
    ser = tmp.groupby(tmp["_d"].dt.to_period("M"))[amount_col].sum().sort_index()
    x = ser.index.to_timestamp()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(x, ser.values, marker="o", linewidth=1.5)
    p = Path(outdir) / cfg.get("filename", "sales/monthly_revenue.png")
    title = cfg.get("title_ru", f"{amount_label} по месяцам")
    xlabel = cfg.get("xlabel_ru", "Месяц")
    ylabel = cfg.get("ylabel_ru", f"{amount_label}, {cur}")
    img = _save(ax, p, title, xlabel, ylabel)
    cap = f"{amount_label} по месяцам; X — месяц; Y — {amount_label}, {cur}."
    return (img, cap)


def _monthly_revenue_by_source(df, cfg, outdir, cur, amount_label):
    date_col = cfg.get("date_col", "order_date")
    amount_col = cfg.get("amount_col", "amount")
    if "source" not in df.columns:
        return None
    d = pd.to_datetime(df[date_col], errors="coerce")
    tmp = df.assign(_d=d).dropna(subset=["_d", amount_col, "source"])
    g = (
        tmp.groupby([tmp["_d"].dt.to_period("M"), "source"])[amount_col]
        .sum()
        .sort_index()
    )

    styles = [
        {"linestyle": "-", "marker": "o"},
        {"linestyle": "--", "marker": "s"},
        {"linestyle": ":", "marker": "D"},
        {"linestyle": "-.", "marker": "^"},
    ]
    fig, ax = plt.subplots(figsize=(9, 4))
    legend_labels = []
    for i, src in enumerate(sorted(g.index.get_level_values(1).unique())):
        ser = g.xs(src, level=1)
        x = ser.index.to_timestamp()
        style = styles[i % len(styles)]
        ax.plot(x, ser.values, label=str(src), linewidth=1.6, **style)
        legend_labels.append(str(src))

    # пометим совпадающие кривые
    try:
        series_by_src = {
            src: g.xs(src, level=1).values
            for src in sorted(g.index.get_level_values(1).unique())
        }
        dup_pairs = []
        keys = list(series_by_src.keys())
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                if np.array_equal(series_by_src[keys[i]], series_by_src[keys[j]]):
                    dup_pairs.append((keys[i], keys[j]))
        if dup_pairs:
            for a, b in dup_pairs:
                legend_labels[legend_labels.index(b)] = f"{b} (совпадает с {a})"
    except Exception:
        pass

    handles, _ = ax.get_legend_handles_labels()
    ax.legend(handles, legend_labels, title="Источник", frameon=False, ncol=1)

    p = Path(outdir) / cfg.get("filename", "sales/monthly_revenue_by_source.png")
    title = cfg.get("title_ru", f"{amount_label} по месяцам и источникам")
    xlabel = cfg.get("xlabel_ru", "Месяц")
    ylabel = cfg.get("ylabel_ru", f"{amount_label}, {cur}")
    img = _save(ax, p, title, xlabel, ylabel)
    cap = f"{amount_label} по месяцам с разбивкой по источникам; X — месяц; Y — {amount_label}, {cur}. Совпадающие кривые помечены."
    return (img, cap)


def _source_share_pie(df, cfg, outdir):
    if "source" not in df.columns:
        return None
    ser = df["source"].fillna("NA").value_counts()

    fig, ax = plt.subplots(figsize=(5.8, 5.8))
    ax.pie(ser.values, labels=ser.index.astype(str), autopct="%1.1f%%")
    ax.set_aspect("equal", adjustable="box")
    p = Path(outdir) / cfg.get("filename", "sales/source_share_pie.png")
    title = cfg.get("title_ru", "Доля записей по источникам")
    img = _save(ax, p, title, "", "")
    cap = "Доли источников в объединённом наборе."
    return (img, cap)


def _cumulative_revenue_by_source(df, cfg, outdir, cur, amount_label):
    date_col = cfg.get("date_col", "order_date")
    amount_col = cfg.get("amount_col", "amount")
    if "source" not in df.columns:
        return None
    d = pd.to_datetime(df[date_col], errors="coerce")
    tmp = df.assign(_d=d).dropna(subset=["_d", amount_col, "source"])
    g = tmp.groupby([tmp["_d"].dt.floor("D"), "source"])[amount_col].sum().sort_index()

    styles = [
        {"linestyle": "-", "marker": None},
        {"linestyle": "--", "marker": None},
        {"linestyle": ":", "marker": None},
        {"linestyle": "-.", "marker": None},
    ]
    fig, ax = plt.subplots(figsize=(9, 4))
    legend_labels = []
    for i, src in enumerate(sorted(g.index.get_level_values(1).unique())):
        ser = g.xs(src, level=1).cumsum()
        style = styles[i % len(styles)]
        ax.plot(ser.index, ser.values, label=str(src), linewidth=1.6, **style)
        legend_labels.append(str(src))

    try:
        series_by_src = {
            src: g.xs(src, level=1).cumsum().values
            for src in sorted(g.index.get_level_values(1).unique())
        }
        dup_pairs = []
        keys = list(series_by_src.keys())
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                if np.array_equal(series_by_src[keys[i]], series_by_src[keys[j]]):
                    dup_pairs.append((keys[i], keys[j]))
        if dup_pairs:
            for a, b in dup_pairs:
                legend_labels[legend_labels.index(b)] = f"{b} (совпадает с {a})"
    except Exception:
        pass

    handles, _ = ax.get_legend_handles_labels()
    ax.legend(handles, legend_labels, title="Источник", frameon=False, ncol=1)

    p = Path(outdir) / cfg.get("filename", "sales/cumulative_revenue_by_source.png")
    title = cfg.get("title_ru", f"Накопленная {amount_label.lower()} по источникам")
    xlabel = cfg.get("xlabel_ru", "Дата")
    ylabel = cfg.get("ylabel_ru", f"Накопленная {amount_label.lower()}, {cur}")
    img = _save(ax, p, title, xlabel, ylabel)
    cap = f"Накопленные суммы по источникам; X — дата; Y — {amount_label} (накопленная), {cur}. Совпадающие кривые помечены."
    return (img, cap)


def _corr_matrix(df, cfg, outdir):
    num = df.drop(
        columns=[c for c in df.columns if c in ID_COLUMNS], errors="ignore"
    ).select_dtypes(include=[np.number])
    if num.empty or num.shape[1] < 2:
        return None
    corr = num.corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(6.8, 5.8))
    im = ax.imshow(corr.values, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=90)
    ax.set_yticks(range(len(corr.index)))
    ax.set_yticklabels(corr.index)
    fig.colorbar(im, ax=ax, label="ρ")
    p = Path(outdir) / cfg.get("filename", "combined/corr_matrix.png")
    title = cfg.get("title_ru", "Корреляционная матрица (без ID)")
    img = _save(ax, p, title, "Признак", "Признак")
    cap = "Корреляции только по содержательным числовым признакам (ID исключены)."
    return (img, cap)


def generate_sales_plots(
    df: pd.DataFrame, plots_cfg: Dict, outdir: Path
) -> List[Tuple[str, str]]:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    cur, amount_label, orders_label, date_fmt, period_txt = _units(plots_cfg, df)
    sales_specs = plots_cfg.get("sales") or []
    combined_specs = plots_cfg.get("combined") or []

    images: List[Tuple[str, str]] = []

    for spec in sales_specs:
        kind = spec.get("kind")
        if kind == "hist" and "amount" in df.columns:
            images.append(_sales_hist(df, spec, outdir, cur, amount_label))
        elif kind == "hist_trim" and "amount" in df.columns:
            images.append(_sales_hist_trim(df, spec, outdir, cur, amount_label))
        elif kind == "box" and "amount" in df.columns:
            images.append(_sales_box(df, spec, outdir, cur, amount_label))
        elif kind == "ts_orders" and "order_date" in df.columns:
            images.append(_ts_orders(df, spec, outdir, orders_label, period_txt))
        elif kind == "top_customers" and "customer_id" in df.columns:
            images.append(_top_customers(df, spec, outdir, orders_label, period_txt))
        elif kind == "monthly_revenue" and {"order_date", "amount"}.issubset(
            df.columns
        ):
            images.append(_monthly_revenue(df, spec, outdir, cur, amount_label))
        elif kind == "monthly_revenue_by_source" and {"order_date", "amount"}.issubset(
            df.columns
        ):
            res = _monthly_revenue_by_source(df, spec, outdir, cur, amount_label)
            if res:
                images.append(res)
        elif kind == "source_share_pie" and "source" in df.columns:
            res = _source_share_pie(df, spec, outdir)
            if res:
                images.append(res)
        elif kind == "cumulative_revenue_by_source" and {
            "order_date",
            "amount",
        }.issubset(df.columns):
            res = _cumulative_revenue_by_source(df, spec, outdir, cur, amount_label)
            if res:
                images.append(res)

    for spec in combined_specs:
        if spec.get("kind") == "corr":
            res = _corr_matrix(df, spec, outdir)
            if res:
                images.append(res)

    return images
