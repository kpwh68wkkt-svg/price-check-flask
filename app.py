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
<title>📱 進貨查價</title>
<meta name="viewport" content="width=device-width, initial-scale=1">

<style>
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial;
  background:#f2f2f2;
  margin:0;
  padding:12px;
}
h1 {
  text-align:center;
  margin-bottom:10px;
}
form {
  margin-bottom:12px;
}
input {
  width:100%;
  padding:16px;
  font-size:20px;
  border-radius:12px;
  border:1px solid #ccc;
}
.card {
  background:white;
  border-radius:14px;
  padding:14px;
  margin-bottom:12px;
  box-shadow:0 2px 6px rgba(0,0,0,.15);
}
.name {
  font-size:20px;
  font-weight:bold;
}
.code {
  color:#666;
  font-size:14px;
}
.price {
  font-size:26px;
  font-weight:bold;
  margin-top:6px;
}
.avg {
  color:#555;
  margin-top:4px;
}
.warn {
  color:red;
  font-weight:bold;
  margin-top:6px;
}
.empty {
  text-align:center;
  color:#999;
  margin-top:30px;
}
</style>
</head>

<body>

<h1>📦 金紙進貨查價</h1>

<form method="get">
  <input
    name="q"
    placeholder="輸入 品名 / 編號（例：香、庫錢、壽金）"
    value="{{ q }}"
    autofocus
  >
</form>

{% if error %}
  <div class="empty">{{ error }}</div>
{% endif %}

{% for _, r in rows.iterrows() %}
<div class="card">
  <div class="name">{{ r["品項名稱"] }}</div>
  <div class="code">{{ r["品項編號"] }}</div>

  <div class="price">
    最新進貨：${{ int(r["最新進貨成本"]) }}
  </div>

  {% if not pd.isna(r["平均進貨成本"]) %}
  <div class="avg">
    平均成本：${{ int(r["平均進貨成本"]) }}
  </div>
  {% endif %}

  {% if r["狀態"] %}
  <div class="warn">{{ r["狀態"] }}</div>
  {% endif %}
</div>
{% endfor %}

{% if rows is not none and len(rows) == 0 %}
  <div class="empty">⚠ 查無資料</div>
{% endif %}

</body>
</html>
"""

def load_data():
    if not os.path.exists(EXCEL_FILE):
        return None, "❌ 找不到 Excel（價格整理.xlsx）"

    xls = pd.ExcelFile(EXCEL_FILE)
    print("📄 偵測到 Sheet：", xls.sheet_names)

    latest = pd.read_excel(EXCEL_FILE, sheet_name="最新進貨成本")
    avg = pd.read_excel(EXCEL_FILE, sheet_name="平均進貨成本")
    up = pd.read_excel(EXCEL_FILE, sheet_name="漲價提醒")

    df = latest.merge(
        avg,
        on=["品項編號", "品項名稱"],
        how="left"
    )

    df["狀態"] = df["品項編號"].isin(up["品項編號"]).apply(
        lambda x: "⚠ 近期漲價" if x else ""
    )

    return df, None

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
    df, error = load_data()

    if df is None:
        return render_template_string(HTML, rows=[], q=q, error=error, pd=pd)

    result = search(df, q)

    return render_template_string(
        HTML,
        rows=result,
        q=q,
        error=None,
        pd=pd
    )

if __name__ == "__main__":
    print("📱 手機查價啟動中…")
    print("👉 瀏覽：http://127.0.0.1:5000 或 雲端網址")
    app.run(host="0.0.0.0", port=5000)
