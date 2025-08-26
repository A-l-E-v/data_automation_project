import pandas as pd
from src.processing.cleaner import (
    impute_missing,
    encode_categorical,
    scale_numeric,
    parse_dates,
)


def test_impute_and_encode_and_scale_and_dates():
    df = pd.DataFrame(
        {
            "num": [1.0, None, 3.0],
            "cat": ["a", "b", "a"],
            "date": ["2024-01-01", "2024-01-02", None],
        }
    )
    df2 = impute_missing(df, strategy="median")
    assert df2["num"].isna().sum() == 0
    df3 = encode_categorical(df2, mode="onehot")
    assert any(c.startswith("cat_") for c in df3.columns)
    df4 = scale_numeric(df3)
    assert abs(df4["num"].mean()) < 1e-6
    df5 = parse_dates(df4, ["date"])
    assert str(df5["date"].dtype).startswith("datetime64")
