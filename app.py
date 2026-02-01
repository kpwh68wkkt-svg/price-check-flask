from flask import Flask, request, render_template_string
import pandas as pd
import os

app = Flask(__name__)

# ===== 基本設定 =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_FILE = os.path.join(BASE_DIR, "價格整理.xlsx")
SHEET_PRIORITY = [
    "最新進價",
    "平均進貨成本",
    "年度進貨成本_年度",
    "整理後明細"
]

HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>📱 進貨查價</title>
<style>
body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 16px; }
input { width: 100%; font-size: 18px; padding: 10px; }
table { width: 100%; border-collapse: collapse; margin-top: 16px; }
th, td { border-bottom: 1px solid #ccc; padding: 8px; text-align: left; }
th { background: #f5f5f5; }
small { color: #888; }
</style>
</head>
<body>
<h2>📦 進貨查價</h2>
<form method="get">
<input name="q" placeholder="輸入關鍵字，例如：錢 / 庫錢 / 壽金" value="{{q}}">
</form>

{% if msg %}
<p style="color:red">{{msg}}</p>
{% endif %}

{% if data %}
<table>
<tr>
{% for c in data[0].keys() %}
<th>{{c}}</th>
{% endfor %}
</tr>
{% for r in data %}
<tr>
{% for v in r.values() %}
<td>{{v}}</td>
{% endfor %}
</tr>
{% endfor %}
</table>
{% endif %}

<small>資料來源：價格整理.xlsx</small>
</body>
</html>
"""

def load_data():
    if not os.path.exists(EXCEL_FILE):
        return None, "❌ 找不到 Excel：價格整理.xlsx"

    xls = pd.ExcelFile(EXCEL_FILE)
    for sheet in SHEET_PRIORITY:
        if sheet in xls.sheet_names:
            df = pd.read_excel(EXCEL_FILE, sheet_name=sheet)
            return df, None

    return None, "❌ 找不到可用的 Sheet"

@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    df, err = load_data()

    if err:
        return render_template_string(HTML, q=q, msg=err, data=None)

    if q:
        mask = df.astype(str).apply(
            lambda s: s.str.contains(q, case=False, na=False)
        ).any(axis=1)
        df = df[mask]

    if df.empty:
        return render_template_string(HTML, q=q, msg="查無資料", data=None)

    data = df.head(50).to_dict("records")
    return render_template_string(HTML, q=q, data=data, msg=None)

if __name__ == "__main__":
    print("📱 手機查價啟動中…")
    print("👉 同 Wi-Fi / 4G 都可（升級後）")
    app.run(host="0.0.0.0", port=5000)
