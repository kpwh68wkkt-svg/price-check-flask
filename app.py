from flask import Flask, request, render_template_string
import pandas as pd
import os

app = Flask(__name__)

EXCEL_FILE = "價格整理.xlsx"

# =====================
# 主查價介面
# =====================
HTML_MAIN = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>📱 進貨查價</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body { font-family: Arial; background:#f5f5f5; padding:10px }
input { width:100%; padding:14px; font-size:18px }
.card {
  background:white; padding:16px; margin:12px 0;
  border-radius:10px; box-shadow:0 2px 6px rgba(0,0,0,.15)
}
.price { font-size:26px; font-weight:bold }
</style>
</head>
<body>

<h2>📦 金紙進貨查價</h2>

<form method="get">
  <input name="q" placeholder="輸入 品名 / 編號" value="{{ q }}">
</form>

{% for r in rows %}
<div class="card">
  <div><b>{{ r["品項名稱"] }}</b>（{{ r["品項編號"] }}）</div>
  <div class="price">${{ r["最新進貨成本"] }}</div>
</div>
{% endfor %}

{% if q and rows|length == 0 %}
<p>⚠ 查無資料</p>
{% endif %}

<hr>
<a href="/up">📈 查看漲價紀錄</a>

</body>
</html>
"""

# =====================
# 漲價查價介面
# =====================
HTML_UP = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>📈 漲價查詢</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body { font-family: Arial; background:#fdf2f2; padding:10px }
.card {
  background:white; padding:16px; margin:12px 0;
  border-radius:10px; box-shadow:0 2px 6px rgba(0,0,0,.2)
}
.warn { color:red; font-weight:bold }
</style>
</head>
<body>

<h2>📈 漲價紀錄查詢</h2>

{% for r in rows %}
<div class="card">
  <div><b>{{ r["品項名稱"] }}</b>（{{ r["品項編號"] }}）</div>
  <div>前次價格：{{ r.get("前次進價", "N/A") }}（{{ r.get("前次日期", "N/A") }}）</div>
  <div class="warn">最新價格：{{ r.get("最新進價", "N/A") }}（{{ r.get("最新日期", "N/A") }}）</div>
</div>
{% endfor %}

{% if rows|length == 0 %}
<p>🎉 目前沒有漲價項目</p>
{% endif %}

<hr>
<a href="/">⬅ 回查價</a>

</body>
</html>
"""

# =====================
# Excel 讀取函數
# =====================
def load_excel():
    if not os.path.exists(EXCEL_FILE):
        return None

    latest = pd.read_excel(EXCEL_FILE, sheet_name="最新進貨成本")
    up = pd.read_excel(EXCEL_FILE, sheet_name="漲價提醒")
    return latest, up

# =====================
# 主查價路由
# =====================
@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    data = load_excel()
    rows = []

    if data:
        latest, _ = data
        if q:
            rows = latest[
                latest["品項名稱"].astype(str).str.contains(q, na=False) |
                latest["品項編號"].astype(str).str.contains(q, na=False)
            ].to_dict("records")

    return render_template_string(HTML_MAIN, rows=rows, q=q)

# =====================
# 漲價查詢路由
# =====================
@app.route("/up")
def show_up():
    data = load_excel()
    rows = []

    if data:
        _, df_up = data
        # 確保欄位名稱對應 HTML 模板
        if "單價" in df_up.columns:
            df_up = df_up.rename(columns={"單價": "最新進價"})
        rows = df_up.to_dict("records")

    return render_template_string(HTML_UP, rows=rows)

# =====================
# 啟動 Flask
# =====================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

