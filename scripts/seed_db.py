"""Seed data/enterprise_ops.db (customers, orders, products, inventory).

Run from the repo root:  uv run python scripts/seed_db.py
Idempotent — deletes and recreates the database file.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "enterprise_ops.db"

SCHEMA = """
CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    city TEXT NOT NULL
);
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    sku TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    unit_price REAL NOT NULL
);
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    sku TEXT NOT NULL REFERENCES products(sku),
    quantity INTEGER NOT NULL,
    order_date TEXT NOT NULL,
    status TEXT NOT NULL,
    total REAL NOT NULL
);
CREATE TABLE inventory (
    id INTEGER PRIMARY KEY,
    sku TEXT NOT NULL REFERENCES products(sku),
    warehouse_city TEXT NOT NULL,
    quantity INTEGER NOT NULL
);
"""

CUSTOMERS = [
    (1, "Apex Logistics", "ops@apex.example", "Seattle"),
    (2, "Northwind Traders", "buyer@northwind.example", "Portland"),
    (3, "Cascade Freight", "dispatch@cascade.example", "Spokane"),
    (4, "Puget Supply Co", "orders@puget.example", "Tacoma"),
    (5, "Evergreen Retail", "stock@evergreen.example", "Bellevue"),
    (6, "Rainier Goods", "hello@rainier.example", "Olympia"),
    (7, "Harborline Inc", "contact@harborline.example", "Bellingham"),
    (8, "Summit Wholesale", "sales@summit.example", "Boise"),
]

PRODUCTS = [
    (1, "SKU-90210", "Industrial Widget", 128.00),
    (2, "SKU-10045", "Packaging Crate", 24.50),
    (3, "SKU-20031", "Hydraulic Coupler", 67.25),
    (4, "SKU-30077", "Conveyor Roller", 41.00),
    (5, "SKU-40012", "Safety Harness", 89.99),
    (6, "SKU-50088", "Barcode Scanner", 215.00),
    (7, "SKU-60023", "Pallet Jack Wheel", 33.75),
    (8, "SKU-70054", "Thermal Label Roll", 12.30),
]

ORDERS = [
    (4492, 1, "SKU-90210", 100, "2026-11-20", "pending", 12800.00),
    (4493, 2, "SKU-10045", 250, "2026-11-18", "shipped", 6125.00),
    (4494, 3, "SKU-20031", 40, "2026-11-19", "delivered", 2690.00),
    (4495, 1, "SKU-30077", 75, "2026-11-21", "pending", 3075.00),
    (4496, 4, "SKU-40012", 30, "2026-11-15", "delivered", 2699.70),
    (4497, 5, "SKU-50088", 10, "2026-11-17", "shipped", 2150.00),
    (4498, 6, "SKU-60023", 120, "2026-11-16", "delivered", 4050.00),
    (4499, 7, "SKU-70054", 500, "2026-11-22", "pending", 6150.00),
    (4500, 8, "SKU-90210", 25, "2026-11-23", "pending", 3200.00),
    (4501, 2, "SKU-40012", 15, "2026-11-23", "pending", 1349.85),
]

INVENTORY = [
    (1, "SKU-90210", "Seattle", 500),
    (2, "SKU-90210", "Portland", 150),
    (3, "SKU-10045", "Seattle", 1200),
    (4, "SKU-20031", "Spokane", 80),
    (5, "SKU-30077", "Seattle", 300),
    (6, "SKU-40012", "Tacoma", 95),
    (7, "SKU-50088", "Bellevue", 22),
    (8, "SKU-70054", "Seattle", 4000),
]


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    DB_PATH.unlink(missing_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA)
        conn.executemany("INSERT INTO customers VALUES (?, ?, ?, ?)", CUSTOMERS)
        conn.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", PRODUCTS)
        conn.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?)", ORDERS)
        conn.executemany("INSERT INTO inventory VALUES (?, ?, ?, ?)", INVENTORY)
        for table in ("customers", "products", "orders", "inventory"):
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"{table}: {count} rows")
    print(f"Seeded {DB_PATH}")


if __name__ == "__main__":
    main()
