import sys
from pathlib import Path
from sqlalchemy import create_engine, text

# добавить корень проекта в sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.utils.logging import getLogger

log = getLogger(__name__)

DSN = "postgresql+psycopg2://ecom_superadmin:ecom_superadmin@localhost:5432/ml_db"


def export_metrics(engine):
    """Выгрузка простых метрик в report_metrics"""
    with engine.begin() as conn:
        # считаем количество строк
        sales_count = conn.execute(text("SELECT COUNT(*) FROM sales")).scalar()
        customers_count = conn.execute(text("SELECT COUNT(*) FROM customers")).scalar()

        # топ-3 стран по продажам (через JOIN с customers)
        top_countries = conn.execute(
            text("""
                SELECT c.country, COUNT(*) AS cnt
                FROM sales s
                JOIN customers c ON s.customer_id = c.customer_id
                GROUP BY c.country
                ORDER BY cnt DESC
                LIMIT 3
            """)
        ).fetchall()

        # сохраняем метрики
        conn.execute(
            text("INSERT INTO report_metrics (metric, value) VALUES (:m, :v)"),
            [{"m": "sales_count", "v": str(sales_count)},
             {"m": "customers_count", "v": str(customers_count)}]
        )
        for country, cnt in top_countries:
            conn.execute(
                text("INSERT INTO report_metrics (metric, value) VALUES (:m, :v)"),
                {"m": f"top_country_{country}", "v": str(cnt)}
            )

    log.info("Метрики успешно выгружены в report_metrics")
    print(f"✓ Метрики: sales={sales_count}, customers={customers_count}, топ страны={top_countries}")


def main():
    try:
        engine = create_engine(DSN)
        log.info("Подключение к БД успешно")
        print("✓ Подключение к БД установлено")

        export_metrics(engine)

        print("✓ Выгрузка метрик завершена успешно")
        log.info("Выгрузка метрик завершена успешно")
    except Exception as e:
        print("✗ Ошибка при выгрузке метрик:", e)
        log.exception("Ошибка при выгрузке метрик")


if __name__ == "__main__":
    main()
