#!/usr/bin/env python3
"""
Генератор sample-данных, имитирующих структуру популярных JSON API (users/products).
Сохраняет:
 - data/processed/api_users.parquet
 - data/processed/api_products.parquet
 - data/raw/customers.csv (упрощённая таблица)
 - data/raw/sales.csv (упрощённая таблица)
"""
from __future__ import annotations
import random
import string
from pathlib import Path
import json
import csv
import pandas as pd
import math
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

RAW.mkdir(parents=True, exist_ok=True)
PROCESSED.mkdir(parents=True, exist_ok=True)

FIRST = [
    "Emily", "Michael", "Sophia", "James", "Emma", "Oliver", "Isabella", "Liam",
    "Mia", "Noah", "Amelia", "Lucas", "Ava", "Mason", "Harper", "Ethan", "Evelyn",
]
LAST = [
    "Johnson", "Williams", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor",
    "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson"
]
CITIES = ["New York", "San Francisco", "Chicago", "Los Angeles", "Austin", "Boston", "Seattle"]
BRANDS = ["Essence", "Glamour", "Velvet Touch", "Chic Cosmetics", "Nail Couture"]
CATEGORIES = ["beauty", "electronics", "home", "sports", "garden", "toys"]

def rand_email(name):
    name = name.lower().replace(" ", ".")
    domains = ["example.com", "x.dummyjson.com", "mail.test"]
    return f"{name}@{random.choice(domains)}"

def rand_ip():
    return ".".join(str(random.randint(1, 250)) for _ in range(4))

def gen_users(n=200):
    rows = []
    now_utc = datetime.now(timezone.utc)
    for i in range(1, n+1):
        fn = random.choice(FIRST)
        ln = random.choice(LAST)
        age = random.randint(18, 70)
        city = random.choice(CITIES)
        birth = (now_utc - timedelta(days=365*age)).date().isoformat()
        user = {
            "id": i,
            "firstName": fn,
            "lastName": ln,
            "age": age,
            "gender": random.choice(["male", "female"]),
            "email": rand_email(f"{fn}.{ln}"),
            "phone": f"+1 {random.randint(200,999)}-{random.randint(200,999)}-{random.randint(1000,9999)}",
            "username": (fn[0]+ln).lower() + str(random.randint(1,99)),
            "birthDate": birth,
            "image": f"https://dummyjson.com/icon/{(fn+ln).lower()}/128",
            "university": random.choice(["Harvard", "MIT", "University of Nowhere", "Oxford"]),
            "ip": rand_ip(),
            "address.city": city,
            "address.postalCode": str(random.randint(10000,99999)),
            "bank.cardNumber": "".join(str(random.randint(0,9)) for _ in range(16)),
            "company.name": f"{random.choice(['Acme','Dooley','Cronin','GmbH','LLC'])} {random.choice(['Corp','Inc','Ltd'])}"
        }
        rows.append(user)
    return pd.DataFrame(rows)


def gen_products(n=180):
    rows = []
    for i in range(1, n+1):
        price = round(random.uniform(5, 500), 2)
        stock = random.randint(0, 500)
        tags = random.sample(["beauty", "makeup", "skincare", "outdoor", "tech", "gaming", "home"], k=random.randint(1,3))
        product = {
            "id": i,
            "title": f"{random.choice(BRANDS)} Product {i}",
            "description": f"Description for product {i}",
            "category": random.choice(CATEGORIES),
            "price": price,
            "discountPercentage": round(random.uniform(0, 30), 2),
            "rating": round(random.uniform(1, 5), 2),
            "stock": stock,
            "tags": json.dumps(tags),
            "brand": random.choice(BRANDS),
            "images": json.dumps([f"https://cdn.example.com/{i}/1.webp"]),
            "thumbnail": f"https://cdn.example.com/{i}/thumb.webp",
            "meta.barcode": str(1000000000000 + i),
        }
        rows.append(product)
    return pd.DataFrame(rows)


def gen_legacy_customers_sales():
    customers = [{"customer_id": i, "country": random.choice(["US","DE","RU","CN","IN"])} for i in range(1, 201)]
    now_utc = datetime.now(timezone.utc)
    sales = []
    for oid in range(1, 1001):
        cid = random.randint(1, 200)
        days = random.randint(0, 365)
        date = (now_utc - timedelta(days=days)).date().isoformat()
        amount = round(random.expovariate(1/80) + random.random()*10, 2)
        sales.append({"order_id": oid, "customer_id": cid, "order_date": date, "amount": amount})
    return customers, sales


def save_parquet(df: pd.DataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        df.to_parquet(path, index=False)
    except Exception:
        df.to_csv(path.with_suffix(".csv"), index=False)


def save_csv(rows, path: Path, fieldnames=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    if fieldnames is None:
        fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    print("Генерация sample данных...")

    users_df = gen_users(208)
    products_df = gen_products(194)

    save_parquet(users_df, PROCESSED / "api_users.parquet")
    save_parquet(products_df, PROCESSED / "api_products.parquet")
    print(f"Saved {len(users_df)} users -> {PROCESSED/'api_users.parquet'}")
    print(f"Saved {len(products_df)} products -> {PROCESSED/'api_products.parquet'}")

    customers, sales = gen_legacy_customers_sales()
    save_csv(customers, RAW / "customers.csv")
    save_csv(sales, RAW / "sales.csv")
    try:
        pd.DataFrame(sales).to_excel(RAW / "sales.xlsx", index=False)
    except Exception:
        pass
    print("Сгенерированы sample данные в data/raw и data/processed")
