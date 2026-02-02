from flask import Flask, request, render_template_string
import pandas as pd
import os

app = Flask(__name__)

EXCEL_FILE = "價格整理.xlsx"

# =========================
# 主查價介面（完全不動）
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
h2 { font-size:28px; }
form {
  display:flex;
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
.name { font-size:24px; font-weight:bold; }
.price { font-size:28px; font-weight:bold; margin-top:6px; }
.avg { font-size:20px; color:#555; }
.warn { margin-top:6px; font-size:20px; color:red; font-weight:bold; }
</style>
</head>
<body>

<h2>📦 金紙進貨查價</h2>

<form method="get">
  <input name="q" placeholder="輸入 品名 / 編號（例：庫錢、壽金、香）" value="{{ q }}">
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
    <div class="warn">{{ r["狀態"] }}</div>
  {% endif %}
</div>
{% endfor %}

<hr>
<a href="/up">📈 查看漲價紀錄</a>

</body>
</html>
"""

# =========================
# 漲價查詢介面（獨立頁面）
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
  background:#fdf2f2;
  padding:16px;
}
.card {
  background:white;
  padding:18px;
  margin-bottom:16px;
  border-radius:12px;
  box-shadow:0 4px 8px rgba(0,0,0,.15);
}
.name { font-size:22px; font-weight:bold; }
.warn { color:red; font-size:22px; font-weight:bold; margin-top:6px; }
</style>
</head>
<body>

<h2>📈 漲價紀錄查詢</h2>

{% for r in rows %}
<div class="card">
  <div class="name">{{ r["品項名稱"] }}（{{ r["品項編號"] }}）</div>
  <div>
    前次價格：${{ r["前次進價"] }}
    （{{ r["前次進價日期"] or "—" }}）
  </div>
  <div class="warn">
    最新價格：${{ r["最新進價"] }}
    （{{ r["最新進價日期"] or "—" }}）
  </div>
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

# =========================
# 資料讀取
# =========================
def load_data():
    if not os.path.exists(EXCEL_FILE):
        return None, None, "❌ 找不到 Excel（價格整理.xlsx）"

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
# 主查價
# =========================
@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    df, _, error = load_data()

    if df is None:
        return render_template_string(HTML_MAIN, rows=[], q=q, error=error)

    if q:
        df = df[
            df["品項名稱"].astype(str).str.contains(q, na=False, regex=False) |
            df["品項編號"].astype(str).str.contains(q, na=False, regex=False)
        ]

    return render_template_string(HTML_MAIN, rows=df, q=q, error=None)

# =========================
# 漲價頁面
# =========================
@app.route("/up")
def up_page():
    _, up, error = load_data()

    if up is None:
        return render_template_string(HTML_UP, rows=[])

    rows = up.to_dict("records")
    return render_template_string(HTML_UP, rows=rows)

# =========================
# 啟動
# =========================
if __name__ == "__main__":
    print("📱 手機查價啟動中…")
    app.run(host="0.0.0.0", port=5000)


