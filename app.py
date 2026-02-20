from flask import Flask, request, render_template_string
import pandas as pd
import time
import os

app = Flask(__name__)
EXCEL_FILE = "價格整理.xlsx"

# ===================== 快取設定 =====================
CACHE_SECONDS = 300  # 最多5分鐘
cache_data = {}
cache_time = {}
cache_file_mtime = 0


# ===================== 主畫面 =====================
MAIN_HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>📱 金紙進貨查價</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:Arial,"Microsoft JhengHei";background:#f0f0f0;padding:16px}
h2{font-size:28px}
a.link{font-size:18px;margin-left:10px}
form{display:flex;gap:10px;margin-bottom:16px}
input{flex:1;padding:14px;font-size:22px;border-radius:8px;border:1px solid #ccc}
button{padding:14px 20px;font-size:20px;border:none;border-radius:8px;background:#007bff;color:white}
.card{background:white;padding:18px;margin-bottom:16px;border-radius:12px;box-shadow:0 4px 8px rgba(0,0,0,.15)}
.name{font-size:24px;font-weight:bold}
.price{font-size:28px;font-weight:bold;margin-top:6px}
.avg{font-size:20px;color:#555}
.warn{margin-top:6px;font-size:20px;color:red;font-weight:bold}
</style>
</head>
<body>
<h2>📦 金紙進貨查價 <a class="link" href="/up">📈 漲價提醒</a> <a class="link" href="/history">📜 進貨紀錄</a></h2>
<form method="get">
<input name="q" placeholder="輸入 品名 / 編號" value="{{ q }}">
<button type="submit">查詢</button>
</form>
{% if error %}<p style="color:red;font-size:20px;">{{ error }}</p>{% endif %}
{% for _, r in rows.iterrows() %}
<div class="card">
<div class="name">{{ r['品項名稱'] }}（{{ r['品項編號'] }}）</div>
<div class="price">最新進貨：${{ r['最新進貨成本'] }}</div>
<div class="avg">平均成本：${{ r['平均進貨成本'] }}</div>
{% if r['狀態'] %}<div class="warn"><a href="/up" style="color:red;text-decoration:none">⚠ 近期漲價</a></div>{% endif %}
</div>
{% endfor %}
</body></html>
"""

# ===================== 漲價頁 =====================
UP_HTML = """
<!doctype html><html><head><meta charset="utf-8">
<title>漲價提醒</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:Arial,"Microsoft JhengHei";background:#f5f5f5;padding:16px}
.card{background:white;padding:16px;margin-bottom:14px;border-radius:12px;box-shadow:0 3px 8px rgba(0,0,0,.15)}
h2{font-size:26px}
a{margin-left:10px}
.name{font-size:22px;font-weight:bold}
.warn{color:red;font-weight:bold;font-size:20px}
</style></head><body>
<h2>📈 漲價提醒 <a href="/">返回主頁</a></h2>
{% for _, r in rows.iterrows() %}
<div class="card">
<div class="name">{{ r['品項名稱'] }}（{{ r['品項編號'] }}）</div>
<div>前次價格：${{ r['前次進價'] }}（{{ r.get('前次進價日期','—') }}）</div>
<div class="warn">最新價格：${{ r['最新進價'] }}（{{ r.get('最新進價日期','—') }}）</div>
</div>
{% endfor %}
</body></html>
"""

# ===================== 歷史紀錄 =====================
HISTORY_HTML = """
<!doctype html><html><head><meta charset="utf-8">
<title>進貨紀錄</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:Arial,"Microsoft JhengHei";background:#fafafa;padding:16px}
h2{font-size:26px}
table{width:100%;border-collapse:collapse;background:white}
th,td{border:1px solid #ccc;padding:8px;text-align:center}
th{background:#eee}
.right{text-align:right}
</style></head><body>
<h2>📜 進貨紀錄 <a href="/">返回主頁</a></h2>
<form method="get">起：<input type="date" name="start"> 迄：<input type="date" name="end"><button>查詢</button></form>
<table>
<tr><th>日期</th><th>編號</th><th>名稱</th><th>數量</th><th>單價</th><th>總價</th></tr>
{% for _, r in rows.iterrows() %}
<tr>
<td>{{ r['日期'] }}</td>
<td>{{ r['品項編號'] }}</td>
<td style="text-align:left">{{ r['品項名稱'] }}</td>
<td class="right">{{ r['數量'] }}</td>
<td class="right">{{ r['單價'] }}</td>
<td class="right">{{ r['金額'] }}</td>
</tr>
{% endfor %}
</table>
</body></html>
"""

# ===================== 快取核心 =====================
def should_reload():
    global cache_file_mtime
    if not os.path.exists(EXCEL_FILE):
        return True

    mtime = os.path.getmtime(EXCEL_FILE)
    if mtime != cache_file_mtime:
        cache_file_mtime = mtime
        return True
    return False


def load_sheet(sheet_name):
    now = time.time()

    if (
        sheet_name in cache_data
        and sheet_name in cache_time
        and (now - cache_time[sheet_name] < CACHE_SECONDS)
        and not should_reload()
    ):
        return cache_data[sheet_name]

    df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name)
    cache_data[sheet_name] = df
    cache_time[sheet_name] = now
    return df


# ===================== 路由 =====================
@app.route('/')
def index():
    q = request.args.get('q', '').strip()

    latest = load_sheet("最新進貨成本")
    avg = load_sheet("平均進貨成本")
    up = load_sheet("漲價提醒")

    df = latest.merge(avg, on=["品項編號", "品項名稱"], how="left")
    df['狀態'] = df['品項編號'].isin(up['品項編號']).map(lambda x: '⚠' if x else '')

    if q:
        df = df[
            df['品項名稱'].astype(str).str.contains(q) |
            df['品項編號'].astype(str).str.contains(q)
        ]

    return render_template_string(MAIN_HTML, rows=df, q=q, error=None)


@app.route('/up')
def up():
    df = load_sheet("漲價提醒")
    return render_template_string(UP_HTML, rows=df)


@app.route('/history')
def history():
    df = load_sheet("整理後明細").copy()
    df['日期'] = pd.to_datetime(df['日期'], errors='coerce')

    s = request.args.get('start')
    e = request.args.get('end')

    if s:
        df = df[df['日期'] >= pd.to_datetime(s)]

    if e:
        df = df[df['日期'] <= pd.to_datetime(e)]

    df['日期'] = df['日期'].dt.strftime('%Y/%m/%d')

    return render_template_string(HISTORY_HTML, rows=df)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
