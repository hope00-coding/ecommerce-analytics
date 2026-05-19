import duckdb
import json

conn = duckdb.connect(r"C:\Users\umutm\ecommerce-analytics\ecommerce.duckdb")

# KPI metrics
total_orders = conn.execute("SELECT COUNT(*) FROM fct_orders").fetchone()[0]
total_revenue = conn.execute("SELECT ROUND(SUM(total_payment),2) FROM fct_orders WHERE order_status='delivered'").fetchone()[0]
total_customers = conn.execute("SELECT COUNT(DISTINCT customer_id) FROM fct_orders").fetchone()[0]
avg_review = conn.execute("SELECT ROUND(AVG(review_score),2) FROM fct_orders WHERE review_score IS NOT NULL").fetchone()[0]
delivered = conn.execute("SELECT COUNT(*) FROM fct_orders WHERE order_status='delivered'").fetchone()[0]
cancelled = conn.execute("SELECT COUNT(*) FROM fct_orders WHERE order_status='canceled'").fetchone()[0]

# Monthly revenue
monthly = conn.execute("""
    SELECT strftime(ordered_at, '%b %Y') as ay,
           strftime(ordered_at, '%Y-%m') as ay_sort,
           ROUND(SUM(total_payment),2) as gelir,
           COUNT(*) as siparis
    FROM fct_orders
    WHERE order_status='delivered' AND ordered_at IS NOT NULL
    GROUP BY ay, ay_sort ORDER BY ay_sort
    LIMIT 12
""").fetchdf()

# Top categories
kategoriler = conn.execute("""
    SELECT category_name,
           ROUND(SUM(total_revenue),2) as gelir,
           SUM(times_ordered) as adet
    FROM dim_products
    WHERE category_name IS NOT NULL
    GROUP BY category_name
    ORDER BY gelir DESC LIMIT 6
""").fetchdf()

# Order status
durumlar = conn.execute("""
    SELECT order_status, COUNT(*) as adet
    FROM fct_orders GROUP BY order_status ORDER BY adet DESC
""").fetchdf()

# Review distribution
reviews = conn.execute("""
    SELECT CAST(review_score AS INT) as puan, COUNT(*) as adet
    FROM fct_orders WHERE review_score IS NOT NULL
    GROUP BY puan ORDER BY puan
""").fetchdf()

# Top cities
sehirler = conn.execute("""
    SELECT city, COUNT(*) as musteri_sayisi
    FROM dim_customers WHERE city IS NOT NULL
    GROUP BY city ORDER BY musteri_sayisi DESC LIMIT 5
""").fetchdf()

# Recent orders (last 10 delivered)
recent = conn.execute("""
    SELECT f.order_id,
           c.city,
           c.state,
           f.order_status,
           ROUND(f.total_payment,2) as tutar,
           CAST(f.ordered_at AS VARCHAR) as tarih,
           f.review_score
    FROM fct_orders f
    LEFT JOIN dim_customers c ON f.customer_id = c.customer_id
    WHERE f.ordered_at IS NOT NULL
    ORDER BY f.ordered_at DESC LIMIT 8
""").fetchdf()

conn.close()

# Prepare data for JS
months = monthly['ay'].tolist()
revenues = monthly['gelir'].tolist()
orders_monthly = monthly['siparis'].tolist()

cat_names = kategoriler['category_name'].tolist()
cat_revenues = kategoriler['gelir'].tolist()

rev_scores = reviews['puan'].tolist()
rev_counts = reviews['adet'].tolist()

status_labels = durumlar['order_status'].tolist()
status_values = durumlar['adet'].tolist()

city_names = sehirler['city'].tolist()
city_counts = sehirler['musteri_sayisi'].tolist()

recent_rows = ""
status_colors = {
    'delivered': ('#d1fae5', '#065f46'),
    'shipped': ('#dbeafe', '#1e40af'),
    'processing': ('#fef3c7', '#92400e'),
    'canceled': ('#fee2e2', '#991b1b'),
    'invoiced': ('#ede9fe', '#4c1d95'),
    'approved': ('#d1fae5', '#065f46'),
    'unavailable': ('#f3f4f6', '#374151'),
    'created': ('#fef3c7', '#92400e'),
}
for _, row in recent.iterrows():
    bg, fg = status_colors.get(str(row['order_status']), ('#f3f4f6', '#374151'))
    stars = '★' * int(row['review_score']) + '☆' * (5 - int(row['review_score'])) if row['review_score'] else '—'
    recent_rows += f"""
    <tr>
      <td style="padding:12px 16px;font-size:13px;color:#374151;font-family:monospace">{str(row['order_id'])[:8]}...</td>
      <td style="padding:12px 16px;font-size:13px;color:#374151">{row['city'] or '—'}, {row['state'] or '—'}</td>
      <td style="padding:12px 16px;font-size:13px;color:#374151">{str(row['tarih'])[:10]}</td>
      <td style="padding:12px 16px">
        <span style="background:{bg};color:{fg};padding:3px 10px;border-radius:20px;font-size:12px;font-weight:500">{row['order_status']}</span>
      </td>
      <td style="padding:12px 16px;font-size:13px;font-weight:600;color:#111827">R$ {row['tutar']:,.2f}</td>
      <td style="padding:12px 16px;font-size:13px;color:#f59e0b">{stars}</td>
    </tr>"""

html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>E-Commerce Analytics</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background:#f0f2f5; color:#111827; display:flex; min-height:100vh; }}

  /* Sidebar */
  .sidebar {{ width:220px; background:#fff; border-right:1px solid #e5e7eb; display:flex; flex-direction:column; padding:24px 0; position:fixed; height:100vh; }}
  .logo {{ padding:0 24px 32px; display:flex; align-items:center; gap:10px; }}
  .logo-icon {{ width:32px; height:32px; background:linear-gradient(135deg,#6366f1,#8b5cf6); border-radius:8px; display:flex; align-items:center; justify-content:center; color:#fff; font-weight:700; font-size:16px; }}
  .logo-text {{ font-weight:700; font-size:16px; color:#111827; }}
  .nav-item {{ display:flex; align-items:center; gap:12px; padding:10px 24px; font-size:14px; color:#6b7280; cursor:pointer; border-left:3px solid transparent; transition:all .15s; }}
  .nav-item:hover {{ background:#f9fafb; color:#111827; }}
  .nav-item.active {{ background:#f5f3ff; color:#6366f1; border-left-color:#6366f1; font-weight:500; }}
  .nav-icon {{ width:18px; height:18px; }}
  .nav-section {{ padding:16px 24px 8px; font-size:11px; font-weight:600; color:#9ca3af; text-transform:uppercase; letter-spacing:.05em; }}
  .sidebar-footer {{ margin-top:auto; padding:16px 24px; font-size:12px; color:#9ca3af; border-top:1px solid #f3f4f6; }}

  /* Main */
  .main {{ margin-left:220px; flex:1; padding:32px; }}
  .topbar {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:28px; }}
  .page-title {{ font-size:22px; font-weight:700; color:#111827; }}
  .page-subtitle {{ font-size:13px; color:#6b7280; margin-top:2px; }}
  .topbar-right {{ display:flex; align-items:center; gap:12px; }}
  .date-badge {{ background:#fff; border:1px solid #e5e7eb; border-radius:8px; padding:6px 14px; font-size:13px; color:#374151; }}
  .avatar {{ width:36px; height:36px; background:linear-gradient(135deg,#6366f1,#8b5cf6); border-radius:50%; display:flex; align-items:center; justify-content:center; color:#fff; font-weight:600; font-size:13px; }}

  /* KPI Cards */
  .kpi-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin-bottom:24px; }}
  .kpi-card {{ background:#fff; border-radius:12px; padding:20px; border:1px solid #f3f4f6; }}
  .kpi-label {{ font-size:12px; color:#9ca3af; font-weight:500; margin-bottom:8px; text-transform:uppercase; letter-spacing:.05em; }}
  .kpi-value {{ font-size:28px; font-weight:700; color:#111827; line-height:1; }}
  .kpi-change {{ font-size:12px; margin-top:6px; display:flex; align-items:center; gap:4px; }}
  .kpi-change.up {{ color:#10b981; }}
  .kpi-change.down {{ color:#ef4444; }}
  .kpi-icon {{ width:40px; height:40px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:18px; margin-bottom:12px; }}

  /* Chart grid */
  .chart-grid {{ display:grid; grid-template-columns:2fr 1fr; gap:16px; margin-bottom:24px; }}
  .chart-grid-3 {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; margin-bottom:24px; }}
  .card {{ background:#fff; border-radius:12px; padding:20px; border:1px solid #f3f4f6; }}
  .card-header {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; }}
  .card-title {{ font-size:14px; font-weight:600; color:#111827; }}
  .card-badge {{ font-size:11px; color:#6b7280; background:#f9fafb; border:1px solid #e5e7eb; padding:3px 10px; border-radius:20px; }}

  /* Table */
  .table-card {{ background:#fff; border-radius:12px; border:1px solid #f3f4f6; overflow:hidden; }}
  table {{ width:100%; border-collapse:collapse; }}
  thead tr {{ background:#f9fafb; border-bottom:1px solid #e5e7eb; }}
  thead th {{ padding:12px 16px; font-size:12px; font-weight:600; color:#6b7280; text-align:left; text-transform:uppercase; letter-spacing:.05em; }}
  tbody tr {{ border-bottom:1px solid #f3f4f6; transition:background .1s; }}
  tbody tr:hover {{ background:#fafafa; }}
  tbody tr:last-child {{ border-bottom:none; }}

  /* Category bars */
  .cat-item {{ margin-bottom:12px; }}
  .cat-header {{ display:flex; justify-content:space-between; margin-bottom:4px; }}
  .cat-name {{ font-size:12px; color:#374151; font-weight:500; text-transform:capitalize; }}
  .cat-val {{ font-size:12px; color:#6b7280; }}
  .cat-bar-bg {{ height:6px; background:#f3f4f6; border-radius:3px; }}
  .cat-bar {{ height:6px; background:linear-gradient(90deg,#6366f1,#8b5cf6); border-radius:3px; }}

  /* City list */
  .city-item {{ display:flex; justify-content:space-between; align-items:center; padding:8px 0; border-bottom:1px solid #f3f4f6; }}
  .city-item:last-child {{ border-bottom:none; }}
  .city-rank {{ width:22px; height:22px; border-radius:50%; background:#f5f3ff; color:#6366f1; font-size:11px; font-weight:700; display:flex; align-items:center; justify-content:center; }}
</style>
</head>
<body>

<!-- Sidebar -->
<div class="sidebar">
  <div class="logo">
    <div class="logo-icon">E</div>
    <div class="logo-text">Olist Analytics</div>
  </div>
  <div class="nav-section">Main</div>
  <div class="nav-item active">
    <svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
    Analytics
  </div>
  <div class="nav-item">
    <svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"/></svg>
    Siparişler
  </div>
  <div class="nav-item">
    <svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0"/></svg>
    Müşteriler
  </div>
  <div class="nav-item">
    <svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10"/></svg>
    Ürünler
  </div>
  <div class="nav-section">Ayarlar</div>
  <div class="nav-item">
    <svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/></svg>
    Ayarlar
  </div>
  <div class="sidebar-footer">dbt + DuckDB + Python</div>
</div>

<!-- Main Content -->
<div class="main">
  <div class="topbar">
    <div>
      <div class="page-title">Analytics</div>
      <div class="page-subtitle">Olist Brazilian E-Commerce — Tüm zamanlar</div>
    </div>
    <div class="topbar-right">
      <div class="date-badge">2016 – 2018</div>
      <div class="avatar">OL</div>
    </div>
  </div>

  <!-- KPI Cards -->
  <div class="kpi-grid">
    <div class="kpi-card">
      <div class="kpi-icon" style="background:#f5f3ff">📦</div>
      <div class="kpi-label">Toplam Sipariş</div>
      <div class="kpi-value">{total_orders:,}</div>
      <div class="kpi-change up">↑ Tüm zamanlar</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-icon" style="background:#ecfdf5">💰</div>
      <div class="kpi-label">Toplam Gelir</div>
      <div class="kpi-value">R$ {total_revenue/1_000_000:.1f}M</div>
      <div class="kpi-change up">↑ Teslim edilen siparişler</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-icon" style="background:#eff6ff">👥</div>
      <div class="kpi-label">Toplam Müşteri</div>
      <div class="kpi-value">{total_customers:,}</div>
      <div class="kpi-change up">↑ Unique müşteri</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-icon" style="background:#fffbeb">⭐</div>
      <div class="kpi-label">Ort. Review Puanı</div>
      <div class="kpi-value">{avg_review}</div>
      <div class="kpi-change up">↑ 5 üzerinden</div>
    </div>
  </div>

  <!-- Charts Row 1 -->
  <div class="chart-grid">
    <div class="card">
      <div class="card-header">
        <div class="card-title">Aylık Gelir (BRL)</div>
        <div class="card-badge">Son 12 ay</div>
      </div>
      <canvas id="revenueChart" height="100"></canvas>
    </div>
    <div class="card">
      <div class="card-header">
        <div class="card-title">Sipariş Durumu</div>
        <div class="card-badge">{total_orders:,} toplam</div>
      </div>
      <canvas id="statusChart" height="160"></canvas>
    </div>
  </div>

  <!-- Charts Row 2 -->
  <div class="chart-grid-3">
    <div class="card">
      <div class="card-header">
        <div class="card-title">En İyi Kategoriler</div>
        <div class="card-badge">Gelire göre</div>
      </div>
      <div id="catBars"></div>
    </div>
    <div class="card">
      <div class="card-header">
        <div class="card-title">Review Dağılımı</div>
        <div class="card-badge">Puan bazlı</div>
      </div>
      <canvas id="reviewChart" height="180"></canvas>
    </div>
    <div class="card">
      <div class="card-header">
        <div class="card-title">En Kalabalık Şehirler</div>
        <div class="card-badge">Müşteri sayısı</div>
      </div>
      <div id="cityList"></div>
    </div>
  </div>

  <!-- Recent Orders Table -->
  <div class="table-card">
    <div class="card-header" style="padding:16px 20px">
      <div class="card-title">Son Siparişler</div>
      <div class="card-badge">En güncel 8 sipariş</div>
    </div>
    <table>
      <thead>
        <tr>
          <th>Sipariş ID</th>
          <th>Şehir</th>
          <th>Tarih</th>
          <th>Durum</th>
          <th>Tutar</th>
          <th>Review</th>
        </tr>
      </thead>
      <tbody>{recent_rows}</tbody>
    </table>
  </div>
</div>

<script>
const months = {json.dumps(months)};
const revenues = {json.dumps(revenues)};
const catNames = {json.dumps(cat_names)};
const catRevenues = {json.dumps(cat_revenues)};
const revScores = {json.dumps(rev_scores)};
const revCounts = {json.dumps(rev_counts)};
const statusLabels = {json.dumps(status_labels)};
const statusValues = {json.dumps(status_values)};
const cityNames = {json.dumps(city_names)};
const cityCounts = {json.dumps(city_counts)};

// Revenue chart
new Chart(document.getElementById('revenueChart'), {{
  type: 'line',
  data: {{
    labels: months,
    datasets: [{{ label: 'Gelir', data: revenues, borderColor: '#6366f1', backgroundColor: 'rgba(99,102,241,0.08)', fill: true, tension: 0.4, pointRadius: 3, pointBackgroundColor: '#6366f1' }}]
  }},
  options: {{ plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ grid: {{ color: '#f3f4f6' }}, ticks: {{ callback: v => 'R$' + (v/1000).toFixed(0) + 'K' }} }}, x: {{ grid: {{ display: false }} }} }} }}
}});

// Status donut
new Chart(document.getElementById('statusChart'), {{
  type: 'doughnut',
  data: {{
    labels: statusLabels,
    datasets: [{{ data: statusValues, backgroundColor: ['#6366f1','#10b981','#f59e0b','#ef4444','#8b5cf6','#06b6d4','#f97316','#84cc16'], borderWidth: 0 }}]
  }},
  options: {{ plugins: {{ legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }}, padding: 10 }} }} }}, cutout: '65%' }}
}});

// Review bar
new Chart(document.getElementById('reviewChart'), {{
  type: 'bar',
  data: {{
    labels: revScores.map(s => s + ' ★'),
    datasets: [{{ data: revCounts, backgroundColor: ['#ef4444','#f97316','#f59e0b','#84cc16','#10b981'], borderRadius: 6, borderSkipped: false }}]
  }},
  options: {{ plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ grid: {{ color: '#f3f4f6' }}, ticks: {{ callback: v => (v/1000).toFixed(0) + 'K' }} }}, x: {{ grid: {{ display: false }} }} }} }}
}});

// Category bars
const maxRev = Math.max(...catRevenues);
const catContainer = document.getElementById('catBars');
catNames.forEach((name, i) => {{
  const pct = (catRevenues[i] / maxRev * 100).toFixed(0);
  const val = (catRevenues[i] / 1000).toFixed(0);
  catContainer.innerHTML += `
    <div class="cat-item">
      <div class="cat-header">
        <span class="cat-name">${{name.replace(/_/g,' ')}}</span>
        <span class="cat-val">R$${{val}}K</span>
      </div>
      <div class="cat-bar-bg"><div class="cat-bar" style="width:${{pct}}%"></div></div>
    </div>`;
}});

// City list
const cityContainer = document.getElementById('cityList');
cityNames.forEach((city, i) => {{
  cityContainer.innerHTML += `
    <div class="city-item">
      <div style="display:flex;align-items:center;gap:10px">
        <div class="city-rank">${{i+1}}</div>
        <span style="font-size:13px;text-transform:capitalize;color:#374151">${{city}}</span>
      </div>
      <span style="font-size:13px;font-weight:600;color:#6366f1">${{cityCounts[i].toLocaleString()}}</span>
    </div>`;
}});
</script>
</body>
</html>"""

output_path = r"C:\Users\umutm\ecommerce-analytics\dashboard\dashboard.html"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Dashboard hazir! Su dosyayi ac: {output_path}")
