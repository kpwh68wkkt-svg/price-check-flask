# ================= 金紙進貨整理＿最終穩定完整版（含漲價日期補 "-"） =================
# 功能：
# - 支援 raw / raw_YYYY 多年度
# - 支援退貨（負數）
# - 整理後明細 / 退貨明細
# - 最新進價
# - 平均進貨成本
# - 年度進貨成本（年度 / 區間）
# - 漲價提醒（有漲就提醒，含日期）
# - 連續漲價提醒（連 2 次以上，含日期）
# - LINE CSV / LINE PDF
# ================================================================

import pandas as pd
import re, os
from datetime import datetime
from openpyxl.utils import get_column_letter
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ================= 基本設定 =================
INPUT_FILE = "進貨明細.xlsx"
OUT_EXCEL = "價格整理.xlsx"
OUT_LINE_CSV = "LINE_查價表.csv"
OUT_LINE_SINGLE_CSV = "LINE_查價_單品快速.csv"
OUT_LINE_PDF = "LINE_查價表.pdf"
FONT = "msjh.ttf"

# ================= Excel 欄寬 =================
def auto_adjust(ws):
    for col in ws.columns:
        max_len = 10
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            if cell.value:
                t = str(cell.value)
                ln = sum(2 if '\u4e00' <= c <= '\u9fff' else 1 for c in t)
                max_len = max(max_len, ln + 2)
        ws.column_dimensions[col_letter].width = max_len

# ================= 讀取所有 raw / raw_YYYY =================
xls = pd.ExcelFile(INPUT_FILE)
raw_sheets = [s for s in xls.sheet_names if s.lower() == "raw" or s.lower().startswith("raw_")]

rows = []
for sheet in raw_sheets:
    # 為避免多欄出現錯誤，只取第一欄
    raw = pd.read_excel(INPUT_FILE, sheet_name=sheet, header=None, usecols=[0])
    raw.columns = ["raw"]

    if raw.empty:
        continue

    for line in raw["raw"].dropna():
        p = str(line).split()
        if len(p) < 6:
            continue

        d = p[0]
        if re.match(r"\d{3}/\d+/\d+", d):
            y,m,dd = d.split("/")
            dt = datetime(int(y)+1911, int(m), int(dd))
        elif re.match(r"\d{4}/\d+/\d+", d):
            y,m,dd = d.split("/")
            dt = datetime(int(y), int(m), int(dd))
        else:
            continue

        code = p[1]
        qty_unit = p[-3]
        price = float(p[-2])

        q = re.search(r"-?\d+", qty_unit)
        u = re.search(r"[\u4e00-\u9fff]+", qty_unit)
        if not q:
            continue

        qty = int(q.group())
        amount = float(p[-1]) * (-1 if qty < 0 else 1)
        name = "".join(p[2:-3])

        rows.append([
            dt, dt.strftime("%Y/%m/%d"), dt.year,
            code, name, qty, u.group() if u else "",
            price, amount
        ])

df = pd.DataFrame(rows, columns=[
    "日期_dt","日期","年度","品項編號","品項名稱",
    "數量","單位","單價","金額"
]).sort_values("日期_dt").reset_index(drop=True)

# ================= 最新進價（排除退貨） =================
latest = (
    df[df["數量"] > 0]
    .groupby("品項編號", as_index=False)
    .last()[["品項編號","品項名稱","單價","日期"]]
)
latest.columns = ["品項編號","品項名稱","最新進價","最新進貨日"]
latest["最新進價_num"] = latest["最新進價"].round(0).astype(int)

# ================= 平均進貨成本 =================
avg_cost = (
    df.groupby("品項編號", as_index=False)
    .apply(lambda g: pd.Series({
        "品項名稱": g["品項名稱"].iloc[-1],
        "平均進貨成本": (
            (g["單價"] * g["數量"]).sum() / g["數量"].sum()
            if g["數量"].sum() != 0 else 0
        )
    }))
    .reset_index(drop=True)
)
avg_cost["平均進貨成本"] = avg_cost["平均進貨成本"].round(0).astype(int)

# ================= 年度進貨成本 =================
year_cost = (
    df.groupby(["年度","品項編號"], as_index=False)
    .apply(lambda g: pd.Series({
        "品項名稱": g["品項名稱"].iloc[-1],
        "年度進貨成本": (
            (g["單價"] * g["數量"]).sum() / g["數量"].sum()
            if g["數量"].sum() != 0 else 0
        )
    }))
    .reset_index(drop=True)
)
year_cost["年度進貨成本"] = year_cost["年度進貨成本"].round(0).astype(int)

# ================= 漲價提醒（含前次日期 / 最新日期，空補 "-"） =================
up_rows, seq_rows = [], []
for code, g in df[df["數量"] > 0].groupby("品項編號"):
    g = g.sort_values("日期_dt")
    
    # 單次漲價
    if len(g) >= 2:
        p1, d1 = g.iloc[-2]["單價"], g.iloc[-2]["日期"]
        p2, d2 = g.iloc[-1]["單價"], g.iloc[-1]["日期"]
        if p2 > p1:
            up_rows.append([
                code,
                g.iloc[-1]["品項名稱"],
                f"${int(p1)}", d1 if d1 else "-",
                f"${int(p2)}", d2 if d2 else "-"
            ])
    
    # 連續漲價（第一次、第二次、最新）
    if len(g) >= 3:
        p1, p2, p3 = g.iloc[-3]["單價"], g.iloc[-2]["單價"], g.iloc[-1]["單價"]
        d1, d2, d3 = g.iloc[-3]["日期"], g.iloc[-2]["日期"], g.iloc[-1]["日期"]
        if p2 > p1 and p3 > p2:
            seq_rows.append([
                code,
                g.iloc[-1]["品項名稱"],
                f"${int(p1)}", d1 if d1 else "-",
                f"${int(p2)}", d2 if d2 else "-",
                f"${int(p3)}", d3 if d3 else "-"
            ])

df_up = pd.DataFrame(up_rows, columns=[
    "品項編號","品項名稱","前次進價","前次日期","最新進價","最新日期"
])

df_seq = pd.DataFrame(seq_rows, columns=[
    "品項編號","品項名稱",
    "第一次漲價","第一次日期",
    "第二次漲價","第二次日期",
    "最新進價","最新日期"
])

# ================= Excel 輸出 =================
with pd.ExcelWriter(OUT_EXCEL, engine="openpyxl") as writer:
    df_fmt = df.copy()
    df_fmt["單價"] = df_fmt["單價"].round(0).astype(int).astype(str).radd("$")
    df_fmt["金額"] = df_fmt["金額"].round(0).astype(int).astype(str).radd("$")
    df_fmt.drop(columns="日期_dt").to_excel(writer, sheet_name="整理後明細", index=False)

    df[df["數量"] < 0].drop(columns="日期_dt").to_excel(writer, sheet_name="退貨明細", index=False)
    latest.drop(columns="最新進價_num").to_excel(writer, sheet_name="最新進價", index=False)
    avg_cost.to_excel(writer, sheet_name="平均進貨成本", index=False)
    year_cost.to_excel(writer, sheet_name="年度進貨成本", index=False)
    df_up.to_excel(writer, sheet_name="漲價提醒", index=False)
    df_seq.to_excel(writer, sheet_name="連續漲價提醒", index=False)

    for ws in writer.book.worksheets:
        auto_adjust(ws)

# ================= LINE CSV =================
latest.drop(columns="最新進價_num").to_csv(OUT_LINE_CSV, index=False, encoding="utf-8-sig")
latest.drop(columns="最新進價_num").to_csv(OUT_LINE_SINGLE_CSV, index=False, encoding="utf-8-sig")

# ================= LINE PDF =================
pdfmetrics.registerFont(TTFont("MSJH", FONT))
if os.path.exists(OUT_LINE_PDF):
    os.remove(OUT_LINE_PDF)

pdf = SimpleDocTemplate(OUT_LINE_PDF, pagesize=A4)
pdf_data = [latest.drop(columns="最新進價_num").columns.tolist()] + latest.drop(columns="最新進價_num").values.tolist()
table = Table(pdf_data, repeatRows=1)
table.setStyle(TableStyle([
    ('GRID',(0,0),(-1,-1),0.5,colors.black),
    ('FONTNAME',(0,0),(-1,-1),'MSJH'),
    ('BACKGROUND',(0,0),(-1,0),colors.lightgrey)
]))
pdf.build([table])

print("✅ 最終穩定完整版完成（漲價日期補 '-'）")
