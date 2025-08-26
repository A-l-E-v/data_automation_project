import yaml
from pathlib import Path
from src.pipelines.pipeline import run


def test_pipeline_minimal(tmp_path: Path):
    # Готовим мини-конфиг и маленькие CSV
    data_dir = tmp_path / "data/raw"
    (tmp_path / "data/processed").mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "customers.csv").write_text(
        "id,is_vip\n1,0\n2,1\n3,0\n", encoding="utf-8"
    )
    (data_dir / "sales.csv").write_text(
        "amount,order_date\n10,2024-01-01\n20,2024-01-02\n", encoding="utf-8"
    )
    cfg = f"""paths:
  data_raw: "data/raw"
  data_processed: "data/processed"
  models: "models"
  logs: "logs"
  reports_pdf: "reports/pdf"
  reports_excel: "reports/excel"
data_sources:
  csv_files:
    - path: "data/raw/customers.csv"
    - path: "data/raw/sales.csv"
cleaning:
  parse_dates: ["order_date"]
  encode_categorical: "onehot"
  scale_numeric: false
analysis:
  classification:
    enabled: true
    target: "is_vip"
  regression:
    enabled: false
reporting:
  pdf: false
  excel: false
email:
  enabled: false
automation:
  save_to_db: false
"""
    p = tmp_path / "config.yaml"
    p.write_text(cfg, encoding="utf-8")
    res = run(p)
    assert "stats" in res
