from __future__ import annotations
from pathlib import Path
from typing import Dict
import pandas as pd
from src.utils.logging import getLogger
from src.reporting.excel import to_excel_multisheet
from .helpers import ID_COLUMNS

log = getLogger(__name__)


def build_excel(
    df_raw: pd.DataFrame,
    df_clean: pd.DataFrame,
    agg_df: pd.DataFrame,
    metrics_df: pd.DataFrame,
    extra_tables_df: Dict[str, pd.DataFrame],
    excel_cfg: Dict,
) -> str | None:
    excel_path = Path(excel_cfg.get("output", "reports/excel/report.xlsx"))
    try:
        sheets: Dict[str, pd.DataFrame] = {
            "raw_combined": df_raw,
            "sales_cleaned": df_clean,
            "aggregates_by_source": agg_df,
            "metrics": metrics_df,
        }
        bs_all = pd.DataFrame(
            df_clean.drop(
                columns=[c for c in df_clean.columns if c in ID_COLUMNS],
                errors="ignore",
            )
            .select_dtypes(include=["number"])
            .describe()
            .T
        )
        sheets["basic_stats"] = bs_all
        if (
            extra_tables_df.get("rf_importance") is not None
            and not extra_tables_df["rf_importance"].empty
        ):
            sheets["rf_importance"] = extra_tables_df["rf_importance"]
        if (
            extra_tables_df.get("logreg_coeffs") is not None
            and not extra_tables_df["logreg_coeffs"].empty
        ):
            sheets["logreg_coeffs"] = extra_tables_df["logreg_coeffs"]
        to_excel_multisheet(excel_path, sheets, with_conditional_format=True)
        return str(excel_path)
    except Exception as e:
        log.exception("Ошибка при формировании Excel: %s", e)
        return None
