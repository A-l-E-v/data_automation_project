import pandas as pd
from pathlib import Path
from src.io.loader import load_csv, load_excel


def test_load_csv(tmp_path: Path):
    p = tmp_path / "t.csv"
    p.write_text("a,b\n1,2\n3,4\n", encoding="utf-8")
    df = load_csv(p)
    assert df.shape == (2, 2)


def test_load_excel(tmp_path: Path):
    p = tmp_path / "t.xlsx"
    df = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
    df.to_excel(p, index=False)
    out = load_excel(p)
    assert out.shape == (2, 2)
