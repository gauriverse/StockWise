
import sqlite3
from pathlib import Path

import pandas as pd
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

ROOT = Path(__file__).resolve().parent.parent
(ROOT / "excel").mkdir(exist_ok=True)

con = sqlite3.connect(ROOT / "stockwise.db")
sales_m = pd.read_sql_query("""
    SELECT strftime('%Y-%m', sale_date) AS month, fy, region, city, category,
           product_id, sku_name,
           SUM(qty) AS units, SUM(gross_sales) AS gross_sales, SUM(net_revenue) AS net_revenue,
           SUM(cogs) AS cogs, SUM(gross_profit) AS gross_profit
    FROM sales_enriched
    GROUP BY month, fy, region, city, category, product_id, sku_name
""", con)
total = pd.read_sql_query("SELECT SUM(net_revenue) AS n, SUM(qty) AS q FROM sales_enriched", con).iloc[0]
con.close()

money = ["gross_sales", "net_revenue", "cogs", "gross_profit"]
sales_m[money] = sales_m[money].round(2)


assert abs(sales_m["net_revenue"].sum() - total["n"]) < 100, "Net revenue does not reconcile"
assert sales_m["units"].sum() == int(total["q"]), "Units do not reconcile"

data = ROOT / "data"
sheets = {
    "Sales_Monthly":      (sales_m, "tblSales"),
    "Reorder_Analysis":   (pd.read_csv(data / "reorder_analysis.csv"), "tblReorder"),
    "ABC_Analysis":       (pd.read_csv(data / "abc_analysis.csv"), "tblABC"),
    "Dead_Stock":         (pd.read_csv(data / "dead_stock.csv"), "tblDeadStock"),
    "Inventory_Turnover": (pd.read_csv(data / "inventory_turnover.csv"), "tblTurnover"),
}

out = ROOT / "excel" / "StockWise_Data.xlsx"
with pd.ExcelWriter(out, engine="openpyxl") as xw:
    for name, (df, tbl) in sheets.items():
        df.to_excel(xw, sheet_name=name, index=False)
        ws = xw.sheets[name]
        ref = f"A1:{get_column_letter(df.shape[1])}{len(df) + 1}"
        t = Table(displayName=tbl, ref=ref)
        t.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
        ws.add_table(t)
        ws.freeze_panes = "A2"
        for i, col in enumerate(df.columns, 1):
            width = max(len(str(col)), df[col].astype(str).str.len().max()) + 2
            ws.column_dimensions[get_column_letter(i)].width = min(width, 40)
        print(f"{name}: {len(df):,} rows")

print("saved ->", out)