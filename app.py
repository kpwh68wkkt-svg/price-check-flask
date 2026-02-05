from flask import Flask, request, render_template_string
import pandas as pd
import os

app = Flask(__name__)

EXCEL_FILE = "價格整理.xlsx"

# ================= 主畫面 =================
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
}
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
  color:red;
  font-weight:bold;
  text-decoration:none;
}
.linkbar a{
  font-size:18px;
  margin-left:10px;
}
</style>
</head>
<body>

<h2>
📦 金紙進貨查價
<span class="linkbar">
<a href="/up">📈 漲價提醒</a>
<a href="/history">📅 進貨明細</a>
</span>
</h2>

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
    <a class="warn" href="/up">⚠ 近期漲價</a>
  {% endif %}
</div>
{% endfor %}

</body>
</html>
"""

# ================= 漲價頁 =================
HTML_UP = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>📈 漲價提醒</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:Arial,"Microsoft JhengHei";background:#f5f5f5;padding:16px;}
.card{background:white;padding:16px;margin-bottom:14px;border-radius:10px;}
.name{font-size:22px;font-weight:bold;}
.old{color:#555;margin-top:6px;}
.new{color:red;font-weight:bold;margin-top:6px;}
</style>
</head>
<body>

<h2>📈 漲價提醒</h2>

{% for _, r in rows.iterrows() %}
<div class="card">
<div class="name">{{ r["品項名稱"] }}（{{ r["品項編號"] }}）</div>
<div class="old">前次價格：${{ r["前次進價"] }}（{{ r["前次進價日期"] }}）</div>
<div class="new">最新價格：${{ r["最新進價"] }}（{{ r["最新進價日期"] }}）</div>
</div>
{% endfor %}

<a href="/">⬅ 回主畫面</a>

</body>
</html>
"""

# ================= 區間進貨明細 =================
HTML_HISTORY = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>📅 進貨明細</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:Arial,"Microsoft JhengHei";background:#f5f5f5;padding:16px;}
form{display:flex;gap:10px;margin-bottom:16px;}
.card{background:white;padding:14px;margin-bottom:10px;border-radius:10px;}
.date{font-weight:bold;}
</style>
</head>
<body>

<h2>📅 區間進貨明細</h2>

<form method="get">
<input type="date" name="start_date" value="{{ start_date }}">
<input type="date" name="end_date" value="{{ end_date }}">
<button type="submit">查詢</button>
</form>

{% for _, r in rows.iterrows() %}
<div class="card">
<div class="date">{{ r["日期"] }}</div>
<div>{{ r["品項名稱"] }}（{{ r["品項編號"] }}）</div>
<div>數量：{{ r["數量"] }}　單價：${{ r["單價"] }}</div>
</div>
{% endfor %}

<a href="/">⬅ 回主畫面</a>

</body>
</html>
"""

# ================= 資料 =================
def load_data():
    if not os.path.exists(EXCEL_FILE):
        return None, "❌ 找不到 Excel"

    latest = pd.read_excel(EXCEL_FILE, sheet_name="最新進貨成本")
    avg = pd.read_excel(EXCEL_FILE, sheet_name="平均進貨成本")
    up = pd.read_excel(EXCEL_FILE, sheet_name="漲價提醒")

    df = latest.merge(avg, on=["品項編號","品項名稱"], how="left")
    df["狀態"] = df["品項編號"].isin(up["品項編號"]).map(lambda x:"⚠ 近期漲價" if x else "")

    return df, None

def search(df, keyword):
    return df[
        df["品項名稱"].astype(str).str.contains(keyword, na=False, regex=False) |
        df["品項編號"].astype(str).str.contains(keyword, na=False, regex=False)
    ]

# ================= routes =================
@app.route("/")
def index():
    q = request.args.get("q","").strip()
    df,error = load_data()

    if df is None:
        return render_template_string(HTML, rows=[], q=q, error=error)

    if q=="":
        return render_template_string(HTML, rows=df, q=q, error=None)

    result = search(df,q)
    if result.empty:
        return render_template_string(HTML, rows=[], q=q, error="⚠ 查無資料")

    return render_template_string(HTML, rows=result, q=q, error=None)

@app.route("/up")
def up():
    df = pd.read_excel(EXCEL_FILE, sheet_name="漲價提醒")
    return render_template_string(HTML_UP, rows=df)

@app.route("/history")
def history():
    start = request.args.get("start_date","")
    end = request.args.get("end_date","")

    df = pd.read_excel(EXCEL_FILE, sheet_name="整理後明細")
    df["日期"]=pd.to_datetime(df["日期"])

    if start:
        df=df[df["日期"]>=pd.to_datetime(start)]
    if end:
        df=df[df["日期"]<=pd.to_datetime(end)]

    df=df.sort_values("日期")
    return render_template_string(HTML_HISTORY, rows=df, start_date=start, end_date=end)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
