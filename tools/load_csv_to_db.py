import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.utils.logging import getLogger

log = getLogger(__name__)

DSN = "postgresql+psycopg2://ecom_superadmin:ecom_superadmin@localhost:5432/ml_db"


def load_table_from_csv(csv_path: str, table_name: str, engine):
    """Загрузка CSV в таблицу Postgres с явными типами"""
    df = pd.read_csv(csv_path)
    log.info("Прочитан CSV %s shape=%s", csv_path, df.shape)

    # Явное указание типов
    if table_name == "sales":
        df = df.astype({
            "order_id": "int",
            "customer_id": "int",
            "order_date": "string",
            "amount": "float"
        })
    elif table_name == "customers":
        df = df.astype({
            "customer_id": "int",
            "country": "string"
        })

    with engine.begin() as conn:
        df.to_sql(table_name, conn, if_exists="replace", index=False)

    log.info("Загружено в таблицу %s rows=%d", table_name, len(df))
    print(f"✓ {table_name}: {len(df)} строк загружено")


def main():
    try:
        engine = create_engine(DSN)
        log.info("Подключение к БД успешно")
        print("✓ Подключение к БД установлено")

        load_table_from_csv("data/raw/sales.csv", "sales", engine)
        load_table_from_csv("data/raw/customers.csv", "customers", engine)

        print("✓ Загрузка CSV завершена успешно")
        log.info("Загрузка CSV завершена успешно")
    except Exception as e:
        print("✗ Ошибка при загрузке CSV:", e)
        log.exception("Ошибка при загрузке CSV")


if __name__ == "__main__":
    main()
