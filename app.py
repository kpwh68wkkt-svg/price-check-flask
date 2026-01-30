from flask import Flask, request, render_template_string
import pandas as pd
import os

app = Flask(__name__)

EXCEL_FILE = "價格整理.xlsx"

HTML_MAIN = """..."""  # 這裡保留你之前的主頁 HTML
HTML_UP = """..."""    # 這裡保留你之前的漲價頁 HTML

def load_excel():
    if not os.path.exists(EXCEL_FILE):
        return None
    latest = pd.read_excel(EXCEL_FILE, sheet_name="最新進貨成本")
    up = pd.read_excel(EXCEL_FILE, sheet_name="漲價提醒")
    return latest, up

@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    data = load_excel()
    rows = []
    if data:
        latest, _ = data
        if q:
            rows = latest[
                latest["品項名稱"].astype(str).str.contains(q, na=False) |
                latest["品項編號"].astype(str).str.contains(q, na=False)
            ].to_dict("records")
    return render_template_string(HTML_MAIN, rows=rows, q=q)

@app.route("/up")
def show_up():
    data = load_excel()
    rows = []
    if data:
        _, df_up = data
        if "單價" in df_up.columns:
            df_up = df_up.rename(columns={"單價": "最新進價"})
        rows = df_up.to_dict("records")
    return render_template_string(HTML_UP, rows=rows)

@app.route("/health")
def health():
    return "OK", 200

# 本地開發用
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
