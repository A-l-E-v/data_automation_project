from __future__ import annotations
from pathlib import Path
from typing import Tuple, Optional

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

ID_COLUMNS = {"order_id", "customer_id"}


def corr_heatmap_png(df: pd.DataFrame, out_path: Path) -> Tuple[Optional[str], str]:
    num = df.drop(
        columns=[c for c in df.columns if c in ID_COLUMNS], errors="ignore"
    ).select_dtypes(include=[np.number])
    if num.empty or num.shape[1] < 2:
        return None, ""
    plt.figure(figsize=(7, 6))
    sns.heatmap(
        num.corr(numeric_only=True), cmap="coolwarm", vmin=-1, vmax=1, annot=False
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=130)
    plt.close()
    cap = "Seaborn: корреляции по числовым признакам (ID исключены)."
    return str(out_path), cap


def pairplot_png(df: pd.DataFrame, out_path: Path) -> Tuple[Optional[str], str]:
    num = df.drop(
        columns=[c for c in df.columns if c in ID_COLUMNS], errors="ignore"
    ).select_dtypes(include=[np.number])
    if num.empty or num.shape[1] < 2:
        return None, ""
    g = sns.pairplot(num, corner=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    g.savefig(out_path, dpi=120)
    plt.close("all")
    cap = "Seaborn PairPlot: распределения и попарные зависимости (ID исключены)."
    return str(out_path), cap
