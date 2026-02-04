from flask import Flask, request, render_template_string
import pandas as pd

app = Flask(__name__)

EXCEL_FILE = "價格整理.xlsx"

# =========================
# 主畫面（查價）
# =========================
@app.route("/", methods=["GET", "POST"])
def index():
    keyword = request.form.get("keyword", "").strip()
    results = []

    if keyword:
        df_latest = pd.read_excel(EXCEL_FILE, sheet_name="最新進貨成本")
        df_avg = pd.read_excel(EXCEL_FILE, sheet_name="平均進貨成本")
        df_up = pd.read_excel(EXCEL_FILE, sheet_name="漲價提醒")

        df = df_latest.merge(
            df_avg, on=["品項編號", "品項名稱"], how="left"
        )

        df["是否漲價"] = df["品項編號"].isin(df_up["品項編號"])

        results = df[
            df["品項名稱"].str.contains(keyword, na=False)
        ].to_dict("records")

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>進貨查價</title>
<style>
body { font-family: Arial; padding:20px; }
.card {
  border:1px solid #ddd;
  border-radius:10px;
  padding:12px;
  margin-bottom:12px;
}
.warn { color:#c00; font-weight:bold; }
</style>
</head>
<body>

<h2 style="display:flex; align-items:center; gap:10px;">
  📦 金紙進貨查價
  <a href="/up"
     style="font-size:14px; color:#c00; text-decoration:none;
            border:1px solid #f5c2c2; padding:4px 10px;
            border-radius:8px; background:#ffe5e5;">
    📈 漲價
  </a>
</h2>

<form method="post">
  <input name="keyword" placeholder="輸入品名" value="{{ keyword }}">
  <button type="submit">查詢</button>
</form>

<hr>

{% for r in results %}
<div class="card">
  <div><b>{{ r["品項名稱"] }}</b>（{{ r["品項編號"] }}）</div>
  <div>最新進貨：${{ r["最新進貨成本"] }}</div>
  <div>平均成本：${{ r["平均進貨成本"] }}</div>

  {% if r["是否漲價"] %}
  <a href="/up" style="text-decoration:none;">
    <div class="warn">⚠ 近期漲價</div>
  </a>
  {% endif %}
</div>
{% endfor %}

</body>
</html>
""", results=results, keyword=keyword)


# =========================
# 漲價頁面
# =========================
@app.route("/up")
def up():
    df = pd.read_excel(EXCEL_FILE, sheet_name="漲價提醒")

    df["前次進價日期"] = df["日期"].shift(1)
    df["最新進價日期"] = df["日期"]

    records = df.to_dict("records")

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>漲價提醒</title>
<style>
body { font-family: Arial; padding:20px; }
.card {
  border:1px solid #f5c2c2;
  background:#fff5f5;
  border-radius:10px;
  padding:12px;
  margin-bottom:12px;
}
.warn { color:#c00; font-weight:bold; }
</style>
</head>
<body>

<h2>📈 漲價提醒</h2>
<a href="/">⬅ 回查價</a>
<hr>

{% for r in records %}
<div class="card">
  <div><b>{{ r["品項名稱"] }}</b>（{{ r["品項編號"] }}）</div>

  <div>
    前次價格：${{ r["前次進價"] }}
    （{{ r["前次進價日期"] or "—" }}）
  </div>

  <div class="warn">
    最新價格：${{ r["最新進價"] }}
    （{{ r["最新進價日期"] or "—" }}）
  </div>
</div>
{% endfor %}

</body>
</html>
""", records=records)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
