# 🛒 E-Commerce Sales & Customer Analytics Platform

> **Analytic Engineering Portfolio Project** — dbt + DuckDB + Python + Plotly

Real-world e-commerce data pipeline built on the Brazilian Olist dataset (~100K orders). Transforms raw, messy CSV files into clean, tested, analysis-ready data models using modern analytics engineering practices.

---

## 🎯 Business Questions Answered

- 📈 What is the monthly revenue trend?
- 🏆 Which product categories generate the most revenue?
- 👥 What does our customer distribution look like across cities?
- ⭐ How satisfied are our customers? (review score analysis)
- 📦 What percentage of orders are delivered on time?

---

## 🏗️ Architecture

```
Raw CSVs (Kaggle)
      │
      ▼
Python Ingestion Script
      │
      ▼
DuckDB (raw_ tables)
      │
      ▼
dbt Staging Models (stg_)
  ├── stg_orders
  ├── stg_customers
  ├── stg_products
  ├── stg_order_items
  ├── stg_payments
  ├── stg_reviews
  └── stg_sellers
      │
      ▼
dbt Mart Models
  ├── fct_orders       ← fact table
  ├── dim_customers    ← customer dimension
  └── dim_products     ← product dimension
      │
      ▼
Plotly HTML Dashboard
```

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| **Python** | Data ingestion, dashboard generation |
| **DuckDB** | Local analytical database (free, no cloud) |
| **dbt Core** | Data transformation & modeling |
| **Plotly** | Interactive dashboard |
| **Kaggle API** | Dataset download automation |

---

## 📊 Dataset

[Brazilian E-Commerce (Olist)](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) — Kaggle

| Table | Rows |
|-------|------|
| orders | ~100K |
| customers | ~99K |
| order items | ~112K |
| payments | ~103K |
| reviews | ~99K |
| products | ~33K |
| sellers | ~3K |
| geolocation | ~1M |

---

## 🚀 How to Run

### 1. Clone & Setup
```bash
git clone https://github.com/YOUR_USERNAME/ecommerce-analytics.git
cd ecommerce-analytics
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. Download Dataset
```bash
# Place your kaggle.json in ~/.kaggle/
kaggle datasets download -d olistbr/brazilian-ecommerce -p data --unzip
```

### 3. Load to DuckDB
```bash
python ingestion/load_to_duckdb.py
```

### 4. Run dbt Models
```bash
cd ecommerce_dbt
dbt run
dbt test
```

### 5. Generate Dashboard
```bash
cd ..
python dashboard/generate_dashboard.py
# Open dashboard/dashboard.html in browser
```

---

## 📁 Project Structure

```
ecommerce-analytics/
├── data/                          # Raw CSV files (gitignored)
├── ingestion/
│   └── load_to_duckdb.py          # CSV → DuckDB loader
├── ecommerce_dbt/
│   ├── models/
│   │   ├── staging/               # stg_ models + sources.yml
│   │   └── marts/                 # fct_ and dim_ models
│   └── dbt_project.yml
├── dashboard/
│   └── generate_dashboard.py      # Plotly HTML dashboard
├── requirements.txt
└── README.md
```

---

## 💡 Key Learnings

- Designed a **Star Schema** with fact and dimension tables
- Applied **dbt best practices**: staging → marts separation, source definitions
- Used **DuckDB** as a cost-free alternative to BigQuery/Snowflake
- Built an end-to-end pipeline from raw CSV to interactive dashboard

---

## 📬 Contact

Built by **[Adın Soyadın]** — [LinkedIn](https://linkedin.com/in/USERNAME)
