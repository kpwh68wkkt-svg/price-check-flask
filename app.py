from flask import Flask, request, render_template_string
import pandas as pd
import os

app = Flask(__name__)

EXCEL_FILE = "價格整理.xlsx"

HTML = """
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>金紙進貨查價</title>
<meta name="viewport" content="width=device-width, initial-scale=1">

<style>
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial;
  background:#f5f5f5;
  margin:0;
  padding:10px;
}

.header {
  font-size:26px;
  font-weight:bold;
  margin-bottom:10px;
}

input {
  width:100%;
  padding:14px;
  font-size:20px;
  border-radius:10px;
  border:1px solid #ccc;
  margin-bottom:12px;
}

.card {
  background:#ffffff;
  border-radius:10px;
  padding:12px;
  margin-bottom:12px;
  box-shadow:0 2px 4px rgba(0,0,0,.15);
}

.name {
  font-size:18px;
  font-weight:bold;
  background:#dcdcdc;
  display:inline-block;
  padding:4px 6px;
  border-radius:4px;
}

.price {
  font-size:22px;
  font-weight:bold;
  margin-top:6px;
  background:#dcdcdc;
  display:inline-block;
  padding:4px 6px;
  border-radius:4px;
}

.avg {
  margin-top:4px;
  font-size:16px;
}

.warn {
  margin-top:6px;
  color:red;
  font-weight:bold;
}
</style>
</head>

<body>

<div class="header">📦 金紙進貨查價</div>

<form method="get">
  <input
    name="q"
    placeholder="輸入 品名 / 編號（例：金箔、香、庫錢）"
    value="{{ q }}"
    autofocus
  >
</form>

{% for _, r in rows.iterrows() %}
<div class="card">
  <div class="name">{{ r["品項名稱"] }}（{{ r["品項編號"] }}）</div>

  <div class="price">
    最新進貨：${{ int(r["最新進貨成本"]) }}
  </div>

  <div class="avg">
    平均成本：${{ "%.1f"|format(r["平均進貨成本"]) }}
  </div>

  {% if r["狀態"] %}
    <div class="warn">{{ r["狀態"] }}</div>
  {% endif %}
</div>
{% endfor %}

{% if rows is not none and len(rows) == 0 %}
<p style="text-align:center;color:#999;">查無資料</p>
{% endif %}

</body>
</html>
"""

def load_data():
    if not os.path.exists(EXCEL_FILE):
        return None

    latest = pd.read_excel(EXCEL_FILE, sheet_name="最新進貨成本")
    avg = pd.read_excel(EXCEL_FILE, sheet_name="平均進貨成本")
    up = pd.read_excel(EXCEL_FILE, sheet_name="漲價提醒")

    df = latest.merge(avg, on=["品項編號", "品項名稱"], how="left")
    df["狀態"] = df["品項編號"].isin(up["品項編號"]).apply(
        lambda x: "⚠ 近期漲價" if x else ""
    )
    return df

def search(df, keyword):
    if not keyword:
        return df
    k = keyword.strip()
    return df[
        df["品項名稱"].astype(str).str.contains(k, case=False, na=False) |
        df["品項編號"].astype(str).str.contains(k, case=False, na=False)
    ]

@app.route("/")
def index():
    q = request.args.get("q", "")
    df = load_data()
    result = search(df, q) if df is not None else []
    return render_template_string(HTML, rows=result, q=q)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
