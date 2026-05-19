import duckdb
import pandas as pd
import os

DB_PATH = r"C:\Users\umutm\ecommerce-analytics\ecommerce.duckdb"
DATA_PATH = r"C:\Users\umutm\ecommerce-analytics\data"

conn = duckdb.connect(DB_PATH)

csv_files = {
    "orders":       "olist_orders_dataset.csv",
    "customers":    "olist_customers_dataset.csv",
    "order_items":  "olist_order_items_dataset.csv",
    "payments":     "olist_order_payments_dataset.csv",
    "reviews":      "olist_order_reviews_dataset.csv",
    "products":     "olist_products_dataset.csv",
    "sellers":      "olist_sellers_dataset.csv",
    "geolocation":  "olist_geolocation_dataset.csv",
    "translations": "product_category_name_translation.csv",
}

for table_name, file_name in csv_files.items():
    file_path = os.path.join(DATA_PATH, file_name)
    print(f"Yukleniyor: {table_name}...")
    conn.execute(f"""
        CREATE OR REPLACE TABLE raw_{table_name} AS
        SELECT * FROM read_csv_auto('{file_path}')
    """)
    count = conn.execute(f"SELECT COUNT(*) FROM raw_{table_name}").fetchone()[0]
    print(f"  ✓ {table_name}: {count:,} satir yuklendi")

conn.close()
print("\nTum tablolar basariyla yuklendi!")