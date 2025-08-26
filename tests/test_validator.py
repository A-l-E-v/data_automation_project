import pandas as pd
import numpy as np
from src.processing.validator import (
    check_duplicates,
    drop_duplicates,
    check_missing,
    check_types,
    detect_outliers_iqr,
    detect_outliers_zscore,
)


def test_duplicates_and_missing():
    df = pd.DataFrame({"a": [1, 1, 2], "b": [np.nan, 0, 1]})
    # Ожидаем 1 дубль: в колонке "a" значение 1 встречается 2 раза -> 1 повтор.
    assert check_duplicates(df) == 1
    miss = check_missing(df)
    assert miss["b"] == 1
    df2 = drop_duplicates(df)
    # По строкам дубликатов нет — размер уменьшаться не должен, но проверим, что функция работает.
    assert len(df2) == 3


def test_types():
    df = pd.DataFrame({"x": [1, 2], "y": ["a", "b"]})
    types = check_types(df)
    assert types["x"].startswith("int") or types["x"].startswith("int64")
    assert types["y"] == "object"


def test_outliers():
    df = pd.DataFrame({"x": [1, 2, 3, 1000]})
    iqr_mask = detect_outliers_iqr(df, ["x"], k=1.5)
    z_mask = detect_outliers_zscore(
        df, ["x"], threshold=2.0
    )  # заниженный порог для маленького набора
    assert iqr_mask["x"].sum() >= 1
    assert z_mask["x"].sum() >= 1
