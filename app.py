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
body {font-family: Arial, "Microsoft JhengHei";background:#f0f0f0;padding:16px;}
h2 {font-size:28px;}
.toplink{font-size:18px;margin-left:10px;}
form {display:flex;gap:10px;margin-bottom:16px;}
input {flex:1;padding:14px;font-size:22px;border-radius:8px;border:1px solid #ccc;}
button {padding:14px 20px;font-size:20px;border:none;border-radius:8px;background:#007bff;color:white;}
.card {background:white;padding:18px;margin-bottom:16px;border-radius:12px;box-shadow:0 4px 8px rgba(0,0,0,.15);} 
.name {font-size:24px;font-weight:bold;}
.price {font-size:28px;font-weight:bold;margin-top:6px;}
.avg {font-size:20px;color:#555;}
.warn {margin-top:6px;font-size:20px;color:red;font-weight:bold;}
</style>
</head>
<body>

<h2>📦 金紙進貨查價 <a class="toplink" href="/up">📈漲價</a> <a class="toplink" href="/history">📅進貨紀錄</a></h2>

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
    <div class="warn"><a href="/up" style="color:red;text-decoration:none;">{{ r["狀態"] }}</a></div>
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
<title>漲價提醒</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:Arial,"Microsoft JhengHei";background:#f0f0f0;padding:16px}
h2{font-size:28px}
.card{background:white;padding:18px;margin-bottom:16px;border-radius:12px;box-shadow:0 4px 8px rgba(0,0,0,.15)}
.name{font-size:24px;font-weight:bold}
</style>
</head>
<body>
<h2>📈 漲價提醒 <a href="/">返回主頁</a></h2>
{% for _, r in rows.iterrows() %}
<div class="card">
<div class="name">{{r['品項名稱']}}（{{r['品項編號']}}）</div>
<div>前次價格：${{r['前次進價']}}（{{r['前次進價日期']}}）</div>
<div style="color:red;font-weight:bold">最新價格：${{r['最新進價']}}（{{r['最新進價日期']}}）</div>
</div>
{% endfor %}
</body></html>
"""

# ================= 進貨紀錄頁 =================
HTML_HISTORY = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>進貨紀錄</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:Arial,"Microsoft JhengHei";background:#f0f0f0;padding:16px}
h2{font-size:28px}
.date{background:#333;color:white;padding:10px;border-radius:10px;margin-top:20px;font-size:22px}
.item{background:white;padding:12px;border-bottom:1px solid #ddd;display:flex;justify-content:space-between;font-size:20px}
</style>
</head>
<body>
<h2>📅 進貨紀錄 <a href="/">返回主頁</a></h2>
<form>
<input type="date" name="start_date" value="{{start_date}}">
<input type="date" name="end_date" value="{{end_date}}">
<button>查詢</button>
</form>
{% for date, group in data.items() %}
<div class="date">{{date}}</div>
{% for r in group %}
<div class="item">
<div>{{r['品項名稱']}}（{{r['品項編號']}}）</div>
<div>{{r['數量']}}</div>
<div>${{r['單價']}}</div>
</div>
{% endfor %}
{% endfor %}
</body></html>
"""

# ================= 資料載入 =================

def load_data():
    latest = pd.read_excel(EXCEL_FILE, sheet_name="最新進貨成本")
    avg = pd.read_excel(EXCEL_FILE, sheet_name="平均進貨成本")
    up = pd.read_excel(EXCEL_FILE, sheet_name="漲價提醒")

    df = latest.merge(avg,on=["品項編號","品項名稱"],how="left")
    df["狀態"] = df["品項編號"].isin(up["品項編號"]).map(lambda x:"⚠ 近期漲價" if x else "")
    return df, up

# ================= 主頁 =================
@app.route("/")
def index():
    q=request.args.get("q","" ).strip()
    df,_=load_data()
    if q:
        df=df[df["品項名稱"].astype(str).str.contains(q)|df["品項編號"].astype(str).str.contains(q)]
    return render_template_string(HTML,rows=df,q=q)

# ================= 漲價 =================
@app.route("/up")
def up():
    _,updf=load_data()
    return render_template_string(HTML_UP,rows=updf)

# ================= 進貨紀錄 =================
@app.route("/history")
def history():
    start=request.args.get("start_date")
    end=request.args.get("end_date")
    df=pd.read_excel(EXCEL_FILE,sheet_name="整理後明細")
    df["日期"]=pd.to_datetime(df["日期"])
    if start: df=df[df["日期"]>=start]
    if end: df=df[df["日期"]<=end]
    grouped={}
    for d,g in df.groupby(df["日期"].dt.strftime("%Y-%m-%d")):
        grouped[d]=g[["品項編號","品項名稱","數量","單價"]].to_dict("records")
    return render_template_string(HTML_HISTORY,data=grouped,start_date=start or "",end_date=end or "")

if __name__=="__main__":
    app.run(host="0.0.0.0",port=5000)

