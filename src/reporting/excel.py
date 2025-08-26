from __future__ import annotations
from pathlib import Path
from typing import Dict
import pandas as pd


def to_excel_multisheet(
    path: Path, sheets: Dict[str, pd.DataFrame], with_conditional_format: bool = False
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
        for name, df in sheets.items():
            df = df if isinstance(df, pd.DataFrame) else pd.DataFrame(df)
            df.to_excel(writer, sheet_name=name[:31], index=False)
        if with_conditional_format and "metrics" in sheets:
            wb = writer.book
            ws = writer.sheets["metrics"[:31]]
            dfm = sheets["metrics"]
            # диапазон (без заголовка)
            rows, cols = dfm.shape
            if rows > 0 and cols > 0:
                data_range = (1, 0, rows, cols - 1)
                # зелёный — лучше (макс R2), красный — хуже (макс RMSE/MAE)
                # простое выделение по столбцам, если они существуют
                headers = [c.lower() for c in dfm.columns]

                def col_idx(colname):
                    try:
                        return headers.index(colname)
                    except ValueError:
                        return None

                # R2 — max good
                r2c = col_idx("r2")
                if r2c is not None:
                    ws.conditional_format(1, r2c, rows, r2c, {"type": "3_color_scale"})
                # RMSE/MAE — чем меньше, тем лучше: выделим красно-зелёной шкалой
                for cname in ("rmse", "mae"):
                    ci = col_idx(cname)
                    if ci is not None:
                        ws.conditional_format(
                            1, ci, rows, ci, {"type": "3_color_scale"}
                        )
