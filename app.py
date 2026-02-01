from flask import Flask, request, render_template_string
import pandas as pd
import os

app = Flask(__name__)

EXCEL_FILE = "價格整理.xlsx"
SHEET_NAME = "最新進貨成本"

HTML = """
<!doctype html>
<title>手機查價</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<h2>📱 金紙查價</h2>
<form method="get">
  <input name="q" placeholder="輸入品項名稱" value="{{ q }}">
  <button type="submit">查詢</button>
</form>
<hr>
{% if rows %}
  <ul>
  {% for r in rows %}
    <li><b>{{ r['品項名稱'] }}</b>：{{ r['最新進貨成本'] }}</li>
  {% endfor %}
  </ul>
{% elif q %}
  <p>查無資料</p>
{% endif %}
"""

@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    rows = []

    if os.path.exists(EXCEL_FILE):
        df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)
        if q:
            mask = df["品項名稱"].astype(str).str.contains(q, case=False, na=False)
            rows = df[mask].to_dict("records")

    return render_template_string(HTML, q=q, rows=rows)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
