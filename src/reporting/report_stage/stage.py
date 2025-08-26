from __future__ import annotations
from typing import Dict, List, Tuple
from pathlib import Path
import pandas as pd
from src.utils.logging import getLogger
from .helpers import aggregates_by_source, overall_metrics, build_pdf_tables
from .charts import build_matplotlib_png, build_seaborn_png, build_plotly_html
from .pdf_builder import build_pdf
from .excel_builder import build_excel

log = getLogger(__name__)


def run_reporting(
    df_raw: pd.DataFrame,
    df_clean: pd.DataFrame,
    cfg: Dict,
    *,
    extra_images_with_captions: List[Tuple[str, str]] | None = None,
    extra_tables: List[Tuple[str, List[List[str]]]] | None = None,
    extra_tables_df: Dict[str, pd.DataFrame] | None = None,
) -> Dict:
    artifacts = {"images": [], "pdf": None, "excel": None, "html": []}
    extra_tables = extra_tables or []
    extra_tables_df = extra_tables_df or {}
    rep_cfg = cfg.get("reporting", {}) or {}
    units = rep_cfg.get("units", {}) or {}
    plots_cfg = rep_cfg.get("plots", {}) or {}
    plots_cfg["parent_units"] = units
    outdir = Path(plots_cfg.get("output_dir", "reports/images"))

    # 1) Matplotlib PNG
    images_with_captions = build_matplotlib_png(df_clean, plots_cfg)
    artifacts["images"] = [p for p, _ in images_with_captions]

    # 2) Seaborn PNG
    seaborn_imgs = build_seaborn_png(df_clean, outdir)
    images_with_captions.extend(seaborn_imgs)
    artifacts["images"].extend([p for p, _ in seaborn_imgs])

    # 3) Plotly HTML
    html_paths = build_plotly_html(df_clean, units)
    artifacts["html"] = html_paths

    # 3.1) ML-дополнения
    if extra_images_with_captions:
        images_with_captions.extend(extra_images_with_captions)
        artifacts["images"].extend([p for p, _ in extra_images_with_captions])

    # 4) Табличные агрегаты
    agg_df = aggregates_by_source(df_clean)
    metrics_df = overall_metrics(df_raw, df_clean)

    pdf_tables = []
    if not agg_df.empty:
        pdf_tables.append(("## Сравнение источников (проверка с данными из БД)", []))
        pdf_tables.append(
            (
                "Таблица",
                [["Источник", "Строк, шт.", "Сумма, руб.", "Средний чек, руб."]]
                + [
                    [
                        str(r.source),
                        int(r.rows),
                        f"{r.amount_sum:.2f}",
                        f"{r.amount_mean:.2f}",
                    ]
                    for r in agg_df.itertuples()
                ],
            )
        )
    pdf_tables.append(("## Числовые сводки (basic_stats)", []))
    pdf_tables.extend(build_pdf_tables(df_clean))
    if extra_tables:
        pdf_tables.append(("## ML-результаты", []))
        pdf_tables.extend(extra_tables)

    # 5) PDF
    pdf_cfg = rep_cfg.get("pdf", {}) or {}
    artifacts["pdf"] = build_pdf(images_with_captions, agg_df, pdf_cfg, pdf_tables)

    # 6) Excel
    excel_cfg = rep_cfg.get("excel", {}) or {}
    artifacts["excel"] = build_excel(
        df_raw, df_clean, agg_df, metrics_df, extra_tables_df, excel_cfg
    )

    if not agg_df.empty:
        log.info("Агрегаты по источникам:\n%s", agg_df.to_string(index=False))
    return artifacts
