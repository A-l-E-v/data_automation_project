from __future__ import annotations
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestRegressor


def rf_importance_table(reg: RandomForestRegressor, feat_cols, top_k: int = 20):
    imps = getattr(reg, "feature_importances_", None)
    if imps is None:
        return ("Важность признаков (RF)", [["нет данных"]], pd.DataFrame())
    pairs = sorted(zip(feat_cols, imps), key=lambda z: z[1], reverse=True)[:top_k]
    header = ["Признак", "Важность"]
    rows = [header] + [[n, f"{v:.6f}"] for n, v in pairs]
    df = pd.DataFrame(pairs, columns=["feature", "importance"])
    return (f"Важность признаков (RandomForest, топ-{top_k})", rows, df)


def logreg_coeffs_table(clf: LogisticRegression, feat_cols, top_k: int = 20):
    coef = getattr(clf, "coef_", None)
    if coef is None or coef.size == 0:
        return (
            "Коэффициенты логистической регрессии",
            [["нет данных"]],
            pd.DataFrame(),
        )
    w = coef.ravel()
    pairs = list(zip(feat_cols, w))
    pairs_sorted = sorted(pairs, key=lambda z: abs(z[1]), reverse=True)[:top_k]
    header = ["Признак", "Коэффициент", "|Коэф.|"]
    rows = [header] + [[n, f"{v:.6f}", f"{abs(v):.6f}"] for n, v in pairs_sorted]
    df = (
        pd.DataFrame(pairs, columns=["feature", "coef"])  # type: ignore
        .assign(abs_coef=lambda d: d["coef"].abs())
        .sort_values("abs_coef", ascending=False)
    )
    return (f"Коэффициенты LogReg (топ-{top_k} по |коэф.|)", rows, df)
