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
  justify-content:space-between;
  align-items:center;
}

a.up {
  font-size:18px;
  text-decoration:none;
  color:#d60000;
  font-weight:bold;
}

form {
  display:flex;
  flex-wrap:wrap;
  gap:10px;
  margin-bottom:16px;
}

input {
  flex:1;
  padding:14px;
  font-size:22px;
  border-radius:8px;
  border:1px solid #ccc;
}

button {
  padding:14px 20px;
  font-size:20px;
  border:none;
  border-radius:8px;
  background:#007bff;
  color:white;
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

.warn a {
  color:red;
  font-weight:bold;
  font-size:20px;
  text-decoration:none;
}
</style>
</head>
<body>

<h2>
  📦 金紙進貨查價
  <a class="up" href="/up">📈 漲價</a>
</h2>

<form method="get">
  <input name="q" placeholder="輸入 品名 / 編號" value="{{ q }}">
  <input type="date" name="start" value="{{ start }}">
  <input type="date" name="end" value="{{ end }}">
  <button type="submit">查詢</button>
</form>

{% if error %}
<p style="color:red; font-size:20px;">{{ error }}</p>
{% endif %}

{% for _, r in rows.iterrows() %}
<div class="card">
  <div class="name">{{ r["品項名稱"] }}（{{ r["品項編號"] }}）</div>
  <div class="price">最新進貨：${{ r["最新進貨成本"] }}</div>
  <div class="avg">平均成本：${{ r["平均進貨成本"] }}</div>

  {% if r["狀態"] %}
  <div class="warn">
    <a href="/up">{{ r["狀態"] }}</a>
  </div>
  {% endif %}
</div>
{% endfor %}

</body>
</html>
"""

UP_HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>📈 漲價提醒</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {
  font-family: Arial, "Microsoft JhengHei";
  background:#f5f5f5;
  padding:16px;
}
.card {
  background:white;
  padding:16px;
  margin-bottom:14px;
  border-radius:10px;
}
.name {
  font-size:22px;
  font-weight:bold;
}
.price {
  font-size:20px;
  color:#d60000;
}
</style>
</head>
<body>

<h2>📈 漲價提醒</h2>

{% for _, r in rows.iterrows() %}
<div class="card">
  <div class="name">{{ r["品項名稱"] }}（{{ r["品項編號"] }}）</div>
  <div class="price">
    前次價格：${{ r["前次進價"] }}（—）<br>
    最新價格：${{ r["最新進價"] }}（{{ r["日期"] or "—" }}）
  </div>
</div>
{% endfor %}

</body>
</html>
"""

def load_data():
    if not os.path.exists(EXCEL_FILE):
        return None, "❌ 找不到 Excel（價格整理.xlsx）"

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

    return df, None

@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    start = request.args.get("start", "")
    end = request.args.get("end", "")

    df, error = load_data()

    if df is None:
        return render_template_string(HTML, rows=[], q=q, start=start, end=end, error=error)

    if q:
        df = df[
            df["品項名稱"].astype(str).str.contains(q, na=False) |
            df["品項編號"].astype(str).str.contains(q, na=False)
        ]

    return render_template_string(
        HTML,
        rows=df,
        q=q,
        start=start,
        end=end,
        error=None
    )

@app.route("/up")
def up():
    df = pd.read_excel(EXCEL_FILE, sheet_name="漲價提醒")
    return render_template_string(UP_HTML, rows=df)

if __name__ == "__main__":
    print("📱 手機查價啟動中…")
    app.run(host="0.0.0.0", port=5000)

