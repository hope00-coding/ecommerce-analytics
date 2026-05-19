import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

conn = duckdb.connect(r"C:\Users\umutm\ecommerce-analytics\ecommerce.duckdb")

monthly = conn.execute("""
    SELECT 
        strftime(ordered_at, '%Y-%m') as ay,
        ROUND(SUM(total_payment), 2)  as gelir,
        COUNT(*)                       as siparis_sayisi
    FROM fct_orders
    WHERE order_status = 'delivered'
    AND ordered_at IS NOT NULL
    GROUP BY ay ORDER BY ay
""").fetchdf()

kategoriler = conn.execute("""
    SELECT 
        category_name,
        ROUND(SUM(total_revenue), 2) as toplam_gelir
    FROM dim_products
    WHERE category_name IS NOT NULL
    GROUP BY category_name
    ORDER BY toplam_gelir DESC
    LIMIT 10
""").fetchdf()

durumlar = conn.execute("""
    SELECT order_status, COUNT(*) as adet
    FROM fct_orders
    GROUP BY order_status ORDER BY adet DESC
""").fetchdf()

reviews = conn.execute("""
    SELECT review_score, COUNT(*) as adet
    FROM fct_orders
    WHERE review_score IS NOT NULL
    GROUP BY review_score ORDER BY review_score
""").fetchdf()

fig = make_subplots(
    rows=2, cols=2,
    specs=[
        [{"type": "xy"}, {"type": "xy"}],
        [{"type": "pie"}, {"type": "xy"}]
    ],
    subplot_titles=(
        "Aylık Gelir (BRL)",
        "En İyi 10 Kategori",
        "Sipariş Durumu",
        "Review Dağılımı"
    )
)

fig.add_trace(go.Scatter(
    x=monthly['ay'], y=monthly['gelir'],
    fill='tozeroy', line=dict(color='#2563eb'),
    name='Gelir'
), row=1, col=1)

fig.add_trace(go.Bar(
    x=kategoriler['toplam_gelir'],
    y=kategoriler['category_name'],
    orientation='h',
    marker_color='#16a34a',
    name='Kategori'
), row=1, col=2)

fig.add_trace(go.Pie(
    labels=durumlar['order_status'],
    values=durumlar['adet'],
    name='Durum'
), row=2, col=1)

fig.add_trace(go.Bar(
    x=reviews['review_score'],
    y=reviews['adet'],
    marker_color='#dc2626',
    name='Review'
), row=2, col=2)

fig.update_layout(
    title_text="E-Ticaret Analitik Dashboard — Olist Brazil",
    title_font_size=20,
    height=800,
    showlegend=False,
    template='plotly_white'
)

fig.write_html(r"C:\Users\umutm\ecommerce-analytics\dashboard\dashboard.html")
print("Dashboard hazir! dashboard/dashboard.html dosyasini ac.")
conn.close()