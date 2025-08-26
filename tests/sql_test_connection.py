import pytest
from sqlalchemy import create_engine, text


def test_postgres_connection():
    dsn = "postgresql+psycopg2://ecom_superadmin:ecom_superadmin@localhost:5432/ml_db"
    engine = create_engine(dsn)
    with engine.connect() as conn:
        r = conn.execute(text("select version()"))
        version = r.scalar()
        assert "PostgreSQL" in version
