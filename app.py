from flask import Flask, request, render_template_string
import pandas as pd
import os

app = Flask(__name__)

EXCEL_FILE = "價格整理.xlsx"

# ==================================================
# 【A】原本的大畫面手機查價介面（完全保留）
# ==================================================
HTML_MAIN = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>📱 進貨查價</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body { font-family: Arial; background:#f5f5f5; padding:12px; }
input {
  width:100%; padding:14px; font-size:20px;
  border-radius:10px; border:1px solid #ccc;
}
.card {
  background:white;
  padding:14px;
  margin:12px 0;
  border-radius:12px;
  box-shadow:0 2px 6px rgba(0,0,0,.15)
}
.price { font-size:26px; font-weight:bold; margin-top:6px }
.avg { color:#555 }
.warn { color:red; font-weight:bold; margin-top:6px }
.link { margin-top:20px; text-align:center }
a { text-decoration:none; font-size:16px }
</style>
</head>
<body>

<h2>📦 金紙進貨查價</h2>

<form method="get">
  <input name="q" placeholder="輸入 品名 / 編號（例：庫錢、壽金）"
         value="{{ q }}" autofocus>
</form>

{% if error %}
<p style="color:red">{{ error }}</p>
{% endif %}

{% for r in rows %}
<div class="card">
  <div><b>{{ r["品項名稱"] }}</b>（{{ r["品項編號"] }}）</div>
  <div class="price">最新進貨：${{ r["最新進貨成本"] }}</div>
  <div class="avg">平均成本：${{ r["平均進貨成本"] }}</div>
  {% if r["狀態"] %}
    <div class="warn">{{ r["狀態"] }}</div>
  {% endif %}
</div>
{% endfor %}

{% if q and rows|length == 0 %}
<p>⚠ 查無資料</p>
{% endif %}

<div class="link">
  👉 <a href="/up">查看漲價查價介面</a>
</div>

</body>
</html>
"""

# ==================================================
# 【B】漲價查價介面（新的 /up）
# ==================================================
HTML_UP = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>📈 漲價查價</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body { font-family: Arial; background:#fff3f3; padding:12px; }
input {
  width:100%; padding:14px; font-size:20px;
  border-radius:10px; border:1px solid #ccc;
}
.card {
  background:white;
  padding:14px;
  margin:12px 0;
  border-radius:12px;
  box-shadow:0 2px 6px rgba(0,0,0,.15)
}
.up { color:red; font-size:22px; font-weight:bold }
.small { color:#666; font-size:14px }
a { text-decoration:none }
</style>
</head>
<body>

<h2>📈 漲價查價</h2>

<form method="get">
  <input name="q" placeholder="輸入品名（例：香、金）"
         value="{{ q }}" autofocus>
</form>

{% for r in rows %}
<div class="card">
  <div><b>{{ r["品項名稱"] }}</b>（{{ r["品項編號"] }}）</div>
  <div class="small">前次：{{ r["前次進價"] }}（{{ r["前次日期"] }}）</div>
  <div class="up">最新：{{ r["最新進價"] }}（{{ r["最新日期"] }}）</div>
</div>
{% endfor %}

{% if q and rows|length == 0 %}
<p>⚠ 查無漲價資料</p>
{% endif %}

<p><a href="/">⬅ 回主查價</a></p>

</body>
</html>
"""

# ==================================================
# 共用資料讀取
# ==================================================
def load_excel():
    if not os.path.exists(EXCEL_FILE):
        return None, "❌ 找不到 Excel（價格整理.xlsx）"

    latest = pd.read_excel(EXCEL_FILE, sheet_name="最新進貨成本")
    avg = pd.read_excel(EXCEL_FILE, sheet_name="平均進貨成本")
    up = pd.read_excel(EXCEL_FILE, sheet_name="漲價提醒")

    df = latest.merge(avg, on=["品項編號", "品項名稱"], how="left")
    df["狀態"] = df["品項編號"].isin(up["品項編號"]).map(
        lambda x: "⚠ 近期漲價" if x else ""
    )

    return df, None


# ==================================================
# 【路由 1】原本查價 /
# ==================================================
@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    df, error = load_excel()

    if df is None:
        return render_template_string(HTML_MAIN, rows=[], q=q, error=error)

    if q:
        df = df[
            df["品項名稱"].astype(str).str.contains(q, na=False) |
            df["品項編號"].astype(str).str.contains(q, na=False)
        ]

    return render_template_string(
        HTML_MAIN,
        rows=df.to_dict("records"),
        q=q,
        error=None
    )


# ==================================================
# 【路由 2】漲價查價 /up（你現在缺的就是這段）
# ==================================================
@app.route("/up")
def up():
    q = request.args.get("q", "").strip()

    df = pd.read_excel(EXCEL_FILE, sheet_name="漲價提醒")

    if q:
        df = df[df["品項名稱"].astype(str).str.contains(q, na=False)]

    return render_template_string(
        HTML_UP,
        rows=df.to_dict("records"),
        q=q
    )


# ==================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
