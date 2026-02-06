# 變動說明：
# 1. 新增 parse_date_range() 支援 2026/2/1-2026/2/28、2026-02-01~2026-02-28
# 2. 修正區間查詢為「含起訖日」
# 3. history 顯示改為進貨單格式：數量/單價/總價 對齊
# 4. 標題加入返回主頁

from flask import Flask, request, render_template_string
import pandas as pd
import os, re

app = Flask(__name__)
EXCEL_FILE = "價格整理.xlsx"

# ---------- 日期解析 ----------

def parse_date_range(text):
    if not text: return None, None
    text = text.replace("~","-")
    m = re.match(r"(\d{4}[/-]\d{1,2}[/-]\d{1,2})-(\d{4}[/-]\d{1,2}[/-]\d{1,2})", text)
    if not m: return None, None
    start = pd.to_datetime(m.group(1), errors="coerce")
    end = pd.to_datetime(m.group(2), errors="coerce")
    if pd.isna(start) or pd.isna(end): return None, None
    return start.normalize(), end.normalize()

# ---------- 主畫面 ----------
HTML_INDEX = """
<h2>📦 金紙進貨查價 <a href='/up'>📈漲價</a> | <a href='/history'>📜區間查詢</a></h2>
<form method=get>
<input name=q value='{{q}}'>
<button>查詢</button>
</form>
{% for _,r in rows.iterrows() %}
<div style='border:1px solid #ccc;margin:8px;padding:8px'>
<b>{{r['品項名稱']}}({{r['品項編號']}})</b><br>
最新：${{r['最新進貨成本']}}<br>
平均：${{r['平均進貨成本']}}<br>
{% if r['狀態'] %}<a href='/up' style='color:red'>⚠ 近期漲價</a>{% endif %}
</div>
{% endfor %}
"""

# ---------- 歷史 ----------
HTML_HISTORY = """
<h2>📜 進貨明細 <a href='/'>返回主頁</a></h2>
<form>
<input name=range placeholder='2026/2/1-2026/2/28' value='{{range}}'>
<button>查詢</button>
</form>
<table border=1 cellpadding=6>
<tr><th>日期</th><th>品項</th><th>數量</th><th>單價</th><th>總價</th></tr>
{% for _,r in rows.iterrows() %}
<tr>
<td>{{r['日期'].date()}}</td>
<td>{{r['品項名稱']}}</td>
<td align=right>{{r['數量']}}</td>
<td align=right>{{r['單價']}}</td>
<td align=right>{{r['總價']}}</td>
</tr>
{% endfor %}
</table>
"""

# ---------- 漲價 ----------
HTML_UP = """
<h2>📈 漲價提醒 <a href='/'>返回主頁</a></h2>
{% for _,r in rows.iterrows() %}
<div style='margin:8px'>
<b>{{r['品項名稱']}}({{r['品項編號']}})</b><br>
前次：${{r['前次價格']}}（{{r['前次日期']}}）<br>
最新：${{r['最新價格']}}（{{r['最新日期']}}）
</div>
{% endfor %}
"""

# ---------- 資料 ----------

def load_base():
    latest = pd.read_excel(EXCEL_FILE, sheet_name="最新進貨成本")
    avg = pd.read_excel(EXCEL_FILE, sheet_name="平均進貨成本")
    up = pd.read_excel(EXCEL_FILE, sheet_name="漲價提醒")
    df = latest.merge(avg,on=["品項編號","品項名稱"],how="left")
    df['狀態']=df['品項編號'].isin(up['品項編號']).map(lambda x:'⚠' if x else '')
    return df

@app.route('/')
def index():
    q=request.args.get('q','')
    df=load_base()
    if q:
        df=df[df['品項名稱'].astype(str).str.contains(q,regex=False)|df['品項編號'].astype(str).str.contains(q,regex=False)]
    return render_template_string(HTML_INDEX,rows=df,q=q)

@app.route('/history')
def history():
    rng=request.args.get('range','')
    df=pd.read_excel(EXCEL_FILE,sheet_name='進貨明細')
    df['日期']=pd.to_datetime(df['日期'],errors='coerce')
    start,end=parse_date_range(rng)
    if start is not None:
        df=df[(df['日期']>=start)&(df['日期']<=end)]
    df['總價']=df['數量']*df['單價']
    return render_template_string(HTML_HISTORY,rows=df.sort_values('日期'),range=rng)

@app.route('/up')
def up():
    df=pd.read_excel(EXCEL_FILE,sheet_name='漲價提醒')
    return render_template_string(HTML_UP,rows=df)

if __name__=='__main__':
    app.run(host='0.0.0.0',port=5000)
