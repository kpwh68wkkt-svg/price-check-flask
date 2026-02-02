from flask import Flask, request, render_template_string
import pandas as pd
import os

app = Flask(__name__)

EXCEL_FILE = "價格整理.xlsx"

# =========================
# 主查價畫面（完全保留你原本風格）
# =========================
HTML_MAIN = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>📱 金紙進貨查價</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {
  font-family: Arial, "Microsoft JhengHei";
  background:#f0f0f0;
  padding:16px;
}
h2 {
  font-size:28px;
  display:flex;
  align-items:center;
  gap:10px;
}
input {
  width:100%;
  padding:14px;
  font-size:22px;
  border-radius:8px;
  border:1px solid #ccc;
  margin-bottom:16px;
}
.card {
  background:white;
  padding:18px;
  margin-bottom:16px;
  border-radius:12px;
  box-shadow:0 4px 8px rgba(0,0,0,.15);
}
.name {
  font-size:24px;
  font-weight:bold;
}
.price {
  font-size:28px;
  font-weight:bold;
  margin-top:6px;
}
.avg {
  font-size:20px;
  color:#555;
}
.warn {
  margin-top:6px;
  font-size:20px;
  color:#c00;
  font-weight:bold;
}
</style>
</head>
<body>

<h2>
  📦 金紙進貨查價
  <a href="/up"
     style="
       font-size:16px;
       color:#c00;
       text-decoration:none;
       border:1px solid #f5c2c2;
       padding:4px 10px;
       border-radius:8px;
       background:#ffe5e5;
     ">
    📈 漲價
  </a>
</h2>

<form method="get">
  <input name="q" placeholder="輸入 品名 / 編號（例：庫錢、壽金、香）" value="{{ q }}">
</form>

{% for _, r in rows.iterrows() %}
<div class="card">
  <div class="name">{{ r["品項名稱"] }}（{{ r["品項編號"] }}）</div>
  <div class="price">最新進貨：${{ r["最新進貨成本"] }}</div>
  <div class="avg">平均成本：${{ r["平均進貨成本"] }}</div>

  {% if r["狀態"] %}
  <a href="/up" style="text-decoration:none;">
    <div class="warn">⚠ 近期漲價</div>
  </a>
  {% endif %}
</div>
{% endfor %}

{% if q and rows|length == 0 %}
<p style="font-size:20px;">⚠ 查無資料</p>
{% endif %}

</body>
</html>
"""

# =========================
# 漲價查詢頁
# =========================
HTML_UP = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>📈 漲價查詢</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {
  font-family: Arial, "Microsoft JhengHei";
  background:#fff2f2;
  padding:16px;
}
.card {
  background:white;
  padding:18px;
  margin-bottom:16px;
  border-radius:12px;
  box-shadow:0 4px 8px rgba(0,0,0,.2);
}
.name {
  font-size:24px;
  font-weight:bold;
}
.old {
  font-size:20px;
}
.new {
  font-size:22px;
  color:#c00;
  font-weight:bold;
}
</style>
</head>
<body>

<h2>📈 漲價紀錄</h2>

{% for r in rows %}
<div class="card">
  <div class="name">{{ r["品項名稱"] }}（{{ r["品項編號"] }}）</div>
  <div class="old">
    前次價格：${{ r["前次進價"] }}
    （{{ r["前次進價日期"] or "—" }}）
  </div>
  <div class="new">
    最新價格：${{ r["最新進價"] }}
    （{{ r["最新進價日期"] or "—" }}）
  </div>
</div>
{% endfor %}

{% if rows|length == 0 %}
<p>🎉 目前沒有漲價項目</p>
{% endif %}

<a href="/" style="font-size:18px;">⬅ 回主畫面</a>

</body>
</html>
"""

# =========================
# 讀取 Excel
# =========================
def load_data():
    if not os.path.exists(EXCEL_FILE):
        return None, None, "❌ 找不到 Excel"

    latest = pd.read_excel(EXCEL_FILE, sheet_name="最新進貨成本")
    avg = pd.read_excel(EXCEL_FILE, sheet_name="平均進貨成本")
    up = pd.read_excel(EXCEL_FILE, sheet_name="漲價提醒")

    df = latest.merge(
        avg,
        on=["品項編號", "品項名稱"],
        how="left"
    )

    df["狀態"] = df["品項編號"].isin(up["品項編號"]).map(
        lambda x: "⚠ 近期漲價" if x else ""
    )

    return df, up, None

# =========================
# 主頁
# =========================
@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    df, _, error = load_data()

    if df is None:
        return render_template_string(HTML_MAIN, rows=[], q=q)

    if q:
        df = df[
            df["品項名稱"].astype(str).str.contains(q, na=False, regex=False) |
            df["品項編號"].astype(str).str.contains(q, na=False, regex=False)
        ]

    return render_template_string(HTML_MAIN, rows=df, q=q)

# =========================
# 漲價頁
# =========================
@app.route("/up")
def up():
    _, up_df, _ = load_data()

    if up_df is None:
        rows = []
    else:
        rows = up_df.rename(columns={
            "日期": "最新進價日期"
        }).to_dict("records")

    return render_template_string(HTML_UP, rows=rows)

# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)




