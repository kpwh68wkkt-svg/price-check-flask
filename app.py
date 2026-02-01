from flask import Flask, request, render_template_string
import pandas as pd
import os

EXCEL_FILE = "價格整理.xlsx"

app = Flask(__name__)

# ================= 讀取資料（自動找可用 Sheet） =================
def load_data():
    if not os.path.exists(EXCEL_FILE):
        print("❌ 找不到 Excel")
        return pd.DataFrame(columns=["品項編號", "品項名稱", "最新進價", "最新進貨日"])

    try:
        xls = pd.ExcelFile(EXCEL_FILE)
        sheets = xls.sheet_names
        print("📄 偵測到 Sheet：", sheets)

        # 優先順序
        for s in ["最新進價", "最新進貨價", "報價單"]:
            if s in sheets:
                df = pd.read_excel(EXCEL_FILE, sheet_name=s)
                return normalize(df)

        # 最後保底：用整理後明細算
        if "整理後明細" in sheets:
            raw = pd.read_excel(EXCEL_FILE, sheet_name="整理後明細")
            raw = raw[raw["數量"] > 0]
            raw = raw.sort_values("日期", ascending=False)
            df = raw.groupby("品項編號", as_index=False).first()
            df = df.rename(columns={
                "單價": "最新進價",
                "日期": "最新進貨日"
            })
            return normalize(df)

        print("❌ 找不到任何可用 Sheet")
        return pd.DataFrame(columns=["品項編號", "品項名稱", "最新進價", "最新進貨日"])

    except Exception as e:
        print("❌ Excel 讀取失敗：", e)
        return pd.DataFrame(columns=["品項編號", "品項名稱", "最新進價", "最新進貨日"])


def normalize(df):
    df = df.fillna("")
    for c in ["品項名稱", "最新進價", "最新進貨日"]:
        if c not in df.columns:
            df[c] = ""
    return df[["品項編號", "品項名稱", "最新進價", "最新進貨日"]]


# ================= HTML =================
HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>手機查價</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI"; padding:20px; }
input { width:100%; padding:14px; font-size:18px; }
button { width:100%; padding:14px; font-size:18px; margin-top:10px; }
.card { border:1px solid #ccc; padding:12px; border-radius:8px; margin-top:10px; }
.name { font-size:18px; font-weight:bold; }
.price { font-size:22px; color:#d33; }
.date { color:#666; font-size:14px; }
</style>
</head>
<body>

<h2>📱 手機查價</h2>

<form method="get">
<input name="q" placeholder="輸入關鍵字（例：錢、庫錢、粗）" value="{{ q }}">
<button type="submit">查詢</button>
</form>

{% if q %}
<hr>
{% if results %}
  {% for r in results %}
  <div class="card">
    <div class="name">{{ r["品項名稱"] }}</div>
    <div class="price">{{ r["最新進價"] }}</div>
    <div class="date">最近進貨：{{ r["最新進貨日"] }}</div>
  </div>
  {% endfor %}
{% else %}
<p>❌ 查無資料</p>
{% endif %}
{% endif %}

</body>
</html>
"""


@app.route("/", methods=["GET"])
def index():
    q = request.args.get("q", "").strip()
    df = load_data()

    results = []
    if q:
        mask = df["品項名稱"].astype(str).str.contains(q, case=False, regex=False)
        results = df[mask].to_dict("records")

    return render_template_string(HTML, q=q, results=results)


if __name__ == "__main__":
    print("📱 手機查價啟動中…")
    print("👉 同 Wi-Fi 手機瀏覽：http://電腦IP:5000")
    app.run(host="0.0.0.0", port=5000)
