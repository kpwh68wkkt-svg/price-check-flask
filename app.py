from flask import Flask, request, render_template_string
import pandas as pd
import os

app = Flask(__name__)

EXCEL_FILE = "價格整理.xlsx"

# =========================================================
# 主頁（完全保持你原本樣式）
# =========================================================
HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>📱 金紙進貨查價</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {font-family: Arial,"Microsoft JhengHei";background:#f0f0f0;padding:16px;}
h2 {font-size:28px;}
form {display:flex;gap:10px;margin-bottom:16px;}
input {flex:1;padding:14px;font-size:22px;border-radius:8px;border:1px solid #ccc;}
button {padding:14px 20px;font-size:20px;border:none;border-radius:8px;background:#007bff;color:white;}
.card {background:white;padding:18px;margin-bottom:16px;border-radius:12px;box-shadow:0 4px 8px rgba(0,0,0,.15);}
.name {font-size:24px;font-weight:bold;}
.price {font-size:28px;font-weight:bold;margin-top:6px;}
.avg {font-size:20px;color:#555;}
.warn {margin-top:6px;font-size:20px;color:red;font-weight:bold;}
.toplink {font-size:18px;margin-left:10px;}
</style>
</head>
<body>

<h2>📦 金紙進貨查價
<a class="toplink" href="/up">📈漲價</a>
<a class="toplink" href="/history">📜進貨紀錄</a>
</h2>

<form method="get">
  <input name="q" placeholder="輸入 品名 / 編號" value="{{ q }}">
  <button type="submit">查詢</button>
</form>

{% for _, r in rows.iterrows() %}
<div class="card">
  <div class="name">{{ r["品項名稱"] }}（{{ r["品項編號"] }}）</div>
  <div class="price">最新進貨：${{ r["最新進貨成本"] }}</div>
  <div class="avg">平均成本：${{ r["平均進貨成本"] }}</div>
  {% if r["狀態"] %}
    <div class="warn"><a href="/up" style="color:red;text-decoration:none;">⚠ 近期漲價</a></div>
  {% endif %}
</div>
{% endfor %}

</body>
</html>
"""

# =========================================================
# 讀資料
# =========================================================
def load_data():
    if not os.path.exists(EXCEL_FILE):
        return None

    latest = pd.read_excel(EXCEL_FILE, sheet_name="最新進貨成本")
    avg = pd.read_excel(EXCEL_FILE, sheet_name="平均進貨成本")
    up = pd.read_excel(EXCEL_FILE, sheet_name="漲價提醒")

    df = latest.merge(avg, on=["品項編號","品項名稱"], how="left")

    df["狀態"] = df["品項編號"].isin(up["品項編號"]).map(
        lambda x: "⚠ 近期漲價" if x else ""
    )
    return df

# =========================================================
# 主頁
# =========================================================
@app.route("/")
def index():
    q = request.args.get("q","").strip()
    df = load_data()

    if df is None:
        return "找不到 Excel"

    if q == "":
        return render_template_string(HTML, rows=df, q=q)

    result = df[
        df["品項名稱"].astype(str).str.contains(q,na=False) |
        df["品項編號"].astype(str).str.contains(q,na=False)
    ]
    return render_template_string(HTML, rows=result, q=q)

# =========================================================
# 漲價頁（安全版）
# =========================================================
@app.route("/up")
def up():
    up = pd.read_excel(EXCEL_FILE, sheet_name="漲價提醒")

    # 容錯：如果沒有日期欄位就補
    if "日期" not in up.columns:
        up["日期"] = "—"

    html = "<h2>📈 漲價提醒 <a href='/'>回主頁</a></h2>"

    for _,r in up.iterrows():
        date = r.get("日期","—")
        html += f"""
        <div style='background:white;padding:15px;margin:10px;border-radius:10px'>
        <b>{r['品項名稱']}（{r['品項編號']}）</b><br>
        前次價格：${r['前次進價']}（{date}）<br>
        <span style='color:red'>最新價格：${r['最新進價']}（{date}）</span>
        </div>
        """

    return html

# =========================================================
# 進貨紀錄（區間查詢）
# =========================================================
@app.route("/history")
def history():
    start = request.args.get("start","")
    end = request.args.get("end","")

    df = pd.read_excel(EXCEL_FILE, sheet_name="整理後明細")

    if start and end:
        df["日期_dt"] = pd.to_datetime(df["日期"])
        s = pd.to_datetime(start)
        e = pd.to_datetime(end)
        df = df[(df["日期_dt"]>=s)&(df["日期_dt"]<=e)]

    html = """
    <h2>📜 進貨紀錄 <a href='/'>回主頁</a></h2>
    <form>
    起：<input name='start' type='date'>
    迄：<input name='end' type='date'>
    <button>查詢</button>
    </form>
    """

    for _,r in df.iterrows():
        html+=f"""
        <div style='background:white;margin:10px;padding:10px;border-radius:10px'>
        {r['日期']} ｜ {r['品項名稱']}（{r['品項編號']}）<br>
        數量：{r['數量']}　
        單價：${r['單價']}　
        金額：${r['金額']}
        </div>
        """

    return html

# =========================================================
if __name__=="__main__":
    app.run(host="0.0.0.0",port=5000)
