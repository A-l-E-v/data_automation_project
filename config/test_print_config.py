# python3 config/test_config.py
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.utils.config import load_config

c = load_config("config/config.yaml")

import json
print("base_dir:", c.base_dir)
print("data_processed:", c.data_processed)
print("reports_pdf:", c.reports_pdf)
print("reports_excel:", c.reports_excel)
print("paths.logs:", c.logs)
print("settings keys:", list(c.settings.keys()))
ds = c.settings.get("data_sources", {})
print("data_sources keys:", list(ds.keys()))
print("csv_files:", ds.get("csv_files"))
print("excel_files:", ds.get("excel_files"))
print("api:", ds.get("api"))