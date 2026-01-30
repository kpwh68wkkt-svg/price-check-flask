from flask import Flask, request, render_template_string
import pandas as pd
import os

app = Flask(__name__)

EXCEL_FILE = "價格整理.xlsx"
SHEET_LATEST = "最新進貨成本"
SHEET_UP = "漲價提醒"

# =========================
# 共用版型（手機大畫面）
# =========================
BASE_HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{{ title }}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI";
  background:#f5f5f5;
  padding:12px;
}
h2 { margin-top:0 }
input {
  width:100%;
  padding:14px;
  font-size:20px;
  box-sizing:border-box;
}
button {
  width:100%;
  padding:12px;
  margin-top:8px;
  font-size:18px;
}
.card {
  background:white;
  padding:14px;
  margin:12px 0;
  border-radius:12px;
  box-shadow:0 2px 6px rgba(0,0,0,.15);
}
.price {
  font-size:26px;
  font-weight:bold;
}
.sub {
  color:#666;
  font-size:16px;
}
.warn {
  color:#c00;
  font-weight:bold;
}
.nav {
  margin-bottom:12px;
}
.nav a {
  margin-right:12px;
  text-decoration:none;
  font-weight:bold;
}
</style>
</head>
<body>

<div class="nav">
  <a href="/">📦 查價</a>
  <a href="/up">📈 漲價查價</a>
</div>

<h2>{{ title }}</h2>

<form method="get">
  <input name="q" placeholder="{{ placeholder }}" value="{{ q }}">
</form>

{% if error %}
<p class="warn">{{ error }}</p>
{% endif %}

{% for r in rows %}
<div class="card">
  {{ card(r) }}
</div>
{% endfor %}

{% if q and not rows %}
<p class="warn">查無資料</p>
{% endif %}

</body>
</html>
"""

# =========================
# A️⃣ 原本「手機查價介面」（保留）
# =========================
@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    rows = []
    error = None

    if not os.path.exists(EXCEL_FILE):
        error = "❌ 找不到 Excel"
    else:
        df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_LATEST)
        if q:
            mask = (
                df["品項名稱"].astype(str).str.contains(q, na=False) |
                df["品項編號"].astype(str).str.contains(q, na=False)
            )
            rows = df[mask].to_dict("records")

    def card(r):
        return f"""
        <div><b>{r['品項名稱']}</b>（{r['品項編號']}）</div>
        <div class="price">💰 {int(r['最新進貨成本'])}</div>
        """

    return render_template_string(
        BASE_HTML,
        title="📱 金紙查價",
        placeholder="輸入品名 / 編號（例：庫錢、壽金）",
        q=q,
        rows=rows,
        error=error,
        card=card
    )

# =========================
# ➕ 新增「漲價查價介面」
# =========================
@app.route("/up")
def up_price():
    q = request.args.get("q", "").strip()
    rows = []
    error = None

    if not os.path.exists(EXCEL_FILE):
        error = "❌ 找不到 Excel"
    else:
        df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_UP)
        if q:
            mask = (
                df["品項名稱"].astype(str).str.contains(q, na=False) |
                df["品項編號"].astype(str).str.contains(q, na=False)
            )
            rows = df[mask].to_dict("records")

    def card(r):
        return f"""
        <div><b>{r['品項名稱']}</b>（{r['品項編號']}）</div>
        <div class="sub">前次進價：{r['前次進價']}（{r.get('前次日期','')}）</div>
        <div class="price warn">⬆ 最新進價：{r['最新進價']}（{r.get('日期','')}）</div>
        """

    return render_template_string(
        BASE_HTML,
        title="📈 漲價查價",
        placeholder="輸入品名 / 編號（查最近漲價）",
        q=q,
        rows=rows,
        error=error,
        card=card
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
