from flask import Flask, request, render_template_string
import pandas as pd
import os

app = Flask(__name__)

EXCEL_FILE = "價格整理.xlsx"
sheet_name="最新進貨成本"

HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>📱 進貨查價</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body { font-family: Arial; background:#f5f5f5; }
input { width:100%; padding:12px; font-size:18px; }
.card {
  background:white;
  padding:12px;
  margin:10px 0;
  border-radius:8px;
  box-shadow:0 2px 4px rgba(0,0,0,.1)
}
.price { font-size:22px; font-weight:bold }
.warn { color:red }
</style>
</head>
<body>

<h2>📦 金紙進貨查價</h2>

<form method="get">
  <input name="q" placeholder="輸入 品名 / 編號（例：庫錢、壽金）" value="{{ q }}">
</form>

{% if error %}
<p style="color:red">{{ error }}</p>
{% endif %}

{% for _, r in rows.iterrows() %}
<div class="card">
  <div><b>{{ r["品項名稱"] }}</b>（{{ r["品項編號"] }}）</div>
  <div class="price">最新進貨：${{ r["最新進貨成本"] }}</div>
  <div>平均成本：${{ r["平均進貨成本"] }}</div>
  {% if r["狀態"] %}
    <div class="warn">{{ r["狀態"] }}</div>
  {% endif %}
</div>
{% endfor %}

</body>
</html>
"""

def load_data():
    if not os.path.exists(EXCEL_FILE):
        return None, "❌ 找不到 Excel（價格整理.xlsx）"

    xls = pd.ExcelFile(EXCEL_FILE)
    print("📄 偵測到 Sheet：", xls.sheet_names)

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

    return df, None

def search(df, keyword):
    if not keyword:
        return df

    keyword = keyword.strip()

    return df[
        df["品項名稱"].astype(str).str.contains(keyword, na=False) |
        df["品項編號"].astype(str).str.contains(keyword, na=False)
    ]

@app.route("/")
def index():
    q = request.args.get("q", "")
    df, error = load_data()

    if df is None:
        return render_template_string(HTML, rows=[], q=q, error=error)

    result = search(df, q)

    return render_template_string(
        HTML,
        rows=result,
        q=q,
        error=None if len(result) else "⚠ 查無資料"
    )

if __name__ == "__main__":
    print("📱 手機查價啟動中…")
    print("👉 同 Wi-Fi 手機瀏覽：http://你的電腦IP:5000")
    app.run(host="0.0.0.0", port=5000)
