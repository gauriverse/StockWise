import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
con = sqlite3.connect(ROOT / "stockwise.db")
df = pd.read_sql_query("""
    SELECT strftime('%Y-%m', sale_date) AS month, fy, region, city, category,
           product_id, sku_name,
           SUM(qty) AS units, SUM(net_revenue) AS net_revenue,
           SUM(cogs) AS cogs, SUM(gross_profit) AS gross_profit
    FROM sales_enriched
    GROUP BY month, fy, region, city, category, product_id, sku_name
""", con)
total_units = con.execute("SELECT SUM(qty) FROM sales").fetchone()[0]
con.close()

assert df["units"].sum() == total_units, "Units do not reconcile"
df.round(2).to_csv(ROOT / "data" / "app_sales_monthly.csv", index=False)
print(f"app_sales_monthly.csv: {len(df):,} rows")