import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
dead_ids = set(pd.read_csv(ROOT / "data" / "dead_stock.csv")["product_id"])

con = sqlite3.connect(ROOT / "stockwise.db")
s = pd.read_sql_query("SELECT sale_date, product_id, qty FROM sales", con)
con.close()

daily = (s[~s["product_id"].isin(dead_ids)]
         .groupby("sale_date", as_index=False)["qty"].sum()
         .rename(columns={"qty": "units"}))
assert len(daily) == 730, "Expected 730 days"
daily.to_csv(ROOT / "data" / "app_daily_units.csv", index=False)
print("app_daily_units.csv:", len(daily), "days")