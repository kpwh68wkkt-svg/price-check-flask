from flask import Flask, request, render_template_string
import pandas as pd
import os

app = Flask(__name__)

EXCEL_FILE = "價格整理.xlsx"

HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>📦 金紙進貨查價</title>
<meta name="viewport" content="width=device-width, initial-scale=1">

<style>
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto;
  background:#f2f2f2;
  margin:0;
  padding:16px;
}
h2 {
  margin:0 0 12px 0;
}
input {
  width:100%;
  padding:14px;
  font-size:20px;
  border-radius:10px;
  border:1px solid #ccc;
  box-sizing:border-box;
}
.card {
  background:#fff;
  border-radius:12px;
  padding:14px;
  margin-top:12px;
  box-shadow:0 2px 6px rgba(0,0,0,.12);
}
.name {
  font-size:18px;
  font-weight:bold;
}
.code {
  color:#666;
  margin-top:2px;
}
.price {
  font-size:24px;
  font-weight:bold;
  margin-top:8px;
}
.avg {
  color:#444;
  margin-top:4px;
}
.warn {
  color:#c00;
  font-weight:bold;
  margin-top:6px;
}
.empty {
  margin-top:20px;
  color:#888;
  text-align:center;
}
</style>
</head>

<body>

<h2>📦 金紙進貨查價</h2>

<form method="get">
  <input
    name="q"
    placeholder="輸入 品名 / 編號（例：金箔、香、庫錢）"
    value="{{ q }}"
    autofocus
  >
</form>

{% if rows is not none and rows|length == 0 %}
  <div class="empty">⚠ 查無資料</div>
{% endif %}

{% for _, r in rows.iterrows() %}
<div class="card">
  <div class="name">{{ r["品項名稱"] }}</div>
  <div class="code">（{{ r["品項編號"] }}）</div>
  <div class="price">最新進貨：${{ r["最新進貨成本"] }}</div>
  <div class="avg">平均成本：${{ r["平均進貨成本"] }}</div>
  {% if r["狀態"] %}
    <div class="warn">{{ r["狀態"] }}</div>
  {% endif %}
</div>
{% endfor %}

</body>
</html>
"""

def load_data():
    if not os.path.exists(EXCEL_FILE):
        return None

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

    return df

def search(df, keyword):
    if not keyword:
        return df

    keyword = keyword.strip()

    return df[
        df["品項名稱"].astype(str).str.contains(keyword, na=False) |
        df["品項編號"].astype(str).str.contains(keyword, na=False)
    ]

@app.route("/")
def index():
    q = request.args.get("q", "")
    df = load_data()

    if df is None:
        return "❌ 找不到 Excel（價格整理.xlsx）"

    result = search(df, q)

    return render_template_string(
        HTML,
        rows=result,
        q=q
    )

if __name__ == "__main__":
    print("📱 手機查價啟動中…")
    app.run(host="0.0.0.0", port=5000)
