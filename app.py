from flask import Flask, request
import pandas as pd
import os

app = Flask(__name__)

EXCEL_FILE = "價格整理.xlsx"

def load_data():
    if not os.path.exists(EXCEL_FILE):
        return None

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

    return df

@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    df = load_data()

    html = """
    <!doctype html>
    <html>
    <head>
    <meta charset="utf-8">
    <title>手機查價</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body style="font-family:Arial;background:#eee;padding:20px;">

    <h1 style="font-size:32px;">📦 金紙進貨查價</h1>

    <form>
      <input name="q" value="{q}"
        placeholder="輸入：香、庫錢、壽金"
        style="
          width:100%;
          font-size:26px;
          padding:16px;
          margin-bottom:16px;
        ">
      <button style="
          width:100%;
          font-size:26px;
          padding:14px;
        ">查詢</button>
    </form>
    """.format(q=q)

    if df is None:
        html += "<p style='font-size:24px;color:red;'>❌ 找不到 Excel</p>"
    else:
        if q:
            df = df[
                df["品項名稱"].astype(str).str.contains(q, na=False) |
                df["品項編號"].astype(str).str.contains(q, na=False)
            ]

        if q and df.empty:
            html += "<p style='font-size:24px;color:red;'>查無資料</p>"

        for _, r in df.iterrows():
            html += f"""
            <div style="
              background:white;
              padding:20px;
              margin:16px 0;
              border-radius:12px;
              font-size:24px;
            ">
              <b style="font-size:26px;">
                {r["品項名稱"]}（{r["品項編號"]}）
              </b><br><br>
              最新進貨：<b>${r["最新進貨成本"]}</b><br>
              平均成本：${r["平均進貨成本"]}<br>
              <span style="color:red;">{r["狀態"]}</span>
            </div>
            """

    html += "</body></html>"
    return html

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
