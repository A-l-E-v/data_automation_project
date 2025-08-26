from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
from src.utils.logging import getLogger
from src.reporting.plots import generate_sales_plots

log = getLogger(__name__)


def build_matplotlib_png(
    df_clean: pd.DataFrame, plots_cfg: Dict
) -> list[tuple[str, str]]:
    outdir = Path(plots_cfg.get("output_dir", "reports/images"))
    images_with_captions = generate_sales_plots(df_clean, plots_cfg, outdir)
    return images_with_captions


def build_seaborn_png(df_clean: pd.DataFrame, outdir: Path) -> list[tuple[str, str]]:
    try:
        from src.reporting.seaborn_plots import corr_heatmap_png, pairplot_png

        seaborn_imgs: list[tuple[str, str]] = []
        p1 = outdir / "combined" / "seaborn_corr.png"
        path1, cap1 = corr_heatmap_png(df_clean, p1)
        if path1:
            seaborn_imgs.append((path1, cap1))
        p2 = outdir / "combined" / "seaborn_pairplot.png"
        path2, cap2 = pairplot_png(df_clean, p2)
        if path2:
            seaborn_imgs.append((path2, cap2))
        return seaborn_imgs
    except Exception as e:
        log.info("Seaborn недоступен или ошибка рендера: %s", e)
        return []


def build_plotly_html(df_clean: pd.DataFrame, units: Dict) -> list[str]:
    try:
        from src.reporting.plotly_charts import monthly_revenue_html, top_customers_html

        html_dir = Path("reports/html")
        html_paths: list[str] = []
        html1 = monthly_revenue_html(
            df_clean,
            "order_date",
            "amount",
            html_dir / "monthly_revenue.html",
            units=units,
        )
        if html1:
            html_paths.append(html1)
        html2 = top_customers_html(
            df_clean,
            "customer_id",
            html_dir / "top_customers.html",
            top_n=10,
            units=units,
        )
        if html2:
            html_paths.append(html2)
        return html_paths
    except Exception as e:
        log.info("Plotly недоступен или ошибка рендера: %s", e)
        return []
