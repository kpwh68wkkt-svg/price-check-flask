from flask import Flask, request
import pandas as pd
import os

app = Flask(__name__)

EXCEL_FILE = "價格整理.xlsx"
SHEET_NAME = "最新進貨成本"

def load_data():
    if not os.path.exists(EXCEL_FILE):
        return None, "❌ 找不到 Excel"

    xls = pd.ExcelFile(EXCEL_FILE)
    if SHEET_NAME not in xls.sheet_names:
        return None, f"❌ 找不到 Sheet：{SHEET_NAME}"

    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)
    return df, None

@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    df, err = load_data()

    if err:
        return err

    if q:
        df = df[
            df["品項名稱"].astype(str).str.contains(q, case=False, na=False) |
            df["品項編號"].astype(str).str.contains(q, case=False, na=False)
        ]

    if df.empty:
        return "查無資料"

    return df.to_html(index=False)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
