from flask import Flask, request, render_template_string
import pandas as pd
import os

app = Flask(__name__)

EXCEL_FILE = "價格整理.xlsx"
SHEET_MAIN = "最新進貨成本"
SHEET_DETAIL = "整理後明細"

HTML = """
<!doctype html>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>📱 金紙查價</title>

<h2>📱 金紙查價</h2>

<form method="get">
  🔍 品項查詢<br>
  <input name="q" placeholder="輸入品項名稱" value="{{ q }}">
  <br><br>

  📅 日期彙總查詢<br>
  <input type="date" name="start" value="{{ start }}">
  ～ 
  <input type="date" name="end" value="{{ end }}">
  <br><br>

  <button type="submit">查詢</button>
</form>

<hr>

{% if price_rows %}
<h3>💰 品項價格</h3>
<ul>
{% for r in price_rows %}
  <li>
    <b>{{ r["品項名稱"] }}</b><br>
    最新進貨：${{ r["最新進貨成本"] }}（{{ r["最新進貨日期"] }}）
  </li>
{% endfor %}
</ul>
{% endif %}

{% if summary_rows %}
<h3>📊 期間進貨彙總</h3>
<ul>
{% for r in summary_rows %}
  <li>
    {{ r["品項名稱"] }}　
    共 {{ r["總數量"] }}　
    ${{ r["總金額"] }}
  </li>
{% endfor %}
</ul>
{% endif %}
"""

@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    start = request.args.get("start", "")
    end = request.args.get("end", "")

    price_rows = []
    summary_rows = []

    if not os.path.exists(EXCEL_FILE):
        return "❌ 找不到 Excel"

    if q:
        df_price = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_MAIN)
        mask = df_price["品項名稱"].astype(str).str.contains(q, case=False, na=False)
        price_rows = df_price[mask].to_dict("records")

    if start:
        df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_DETAIL)
        df["日期_dt"] = pd.to_datetime(df["日期"])

        s = pd.to_datetime(start)
        e = pd.to_datetime(end) if end else s

        df = df[(df["日期_dt"] >= s) & (df["日期_dt"] <= e)]

        summary = (
            df.groupby("品項名稱", as_index=False)
              .agg(總數量=("數量", "sum"), 總金額=("金額", "sum"))
        )

        summary_rows = summary.to_dict("records")

    return render_template_string(
        HTML,
        q=q,
        start=start,
        end=end,
        price_rows=price_rows,
        summary_rows=summary_rows
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
