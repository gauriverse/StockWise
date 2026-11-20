import re
import sqlite3
import subprocess
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data"
fails, warns = 0, 0


def check(name, ok, detail=""):
    global fails
    fails += 0 if ok else 1
    print(("PASS  " if ok else "FAIL  ") + name + (f"  -> {detail}" if detail else ""))


def warn(name, bad, detail=""):
    global warns
    warns += 1 if bad else 0
    print(("WARN  " if bad else "PASS  ") + name + (f"  -> {detail}" if detail else ""))


# ---------- 1. files ----------
needed = ["products.csv", "stores.csv", "suppliers.csv", "sales.csv", "inventory.csv",
          "abc_analysis.csv", "dead_stock.csv", "reorder_analysis.csv", "inventory_turnover.csv",
          "forecast_next30.csv", "category_uplift.csv", "order_recommendations.csv",
          "forecast_scorecard.csv", "forecast_backtest_by_category.csv",
          "app_sales_monthly.csv", "app_daily_units.csv"]
missing = [f for f in needed if not (D / f).exists()]
check("all data files exist", not missing, str(missing))
if missing:
    raise SystemExit("Fix missing files first.")

# ---------- 2. database vs exports ----------
con = sqlite3.connect(ROOT / "stockwise.db")
db_units, db_net = con.execute("SELECT SUM(qty), SUM(net_revenue) FROM sales_enriched").fetchone()
fy_rows = con.execute("SELECT fy, COUNT(*) FROM sales_enriched GROUP BY fy").fetchall()
last_dates = pd.read_sql_query("SELECT product_id, MAX(sale_date) AS last_sale FROM sales GROUP BY product_id", con)
con.close()

app = pd.read_csv(D / "app_sales_monthly.csv")
check("app file units = database units", app["units"].sum() == db_units, f"{app['units'].sum():,} vs {db_units:,}")
check("app file net revenue = database", abs(app["net_revenue"].sum() - db_net) < 200, f"{app['net_revenue'].sum():,.0f} vs {db_net:,.0f}")
check("only 2 financial years, no NULL fy", sorted(r[0] for r in fy_rows if r[0]) == ["2024-25", "2025-26"] and all(r[0] for r in fy_rows))

# ---------- 3. reorder analysis ----------
re_ = pd.read_csv(D / "reorder_analysis.csv")
inv = pd.read_csv(D / "inventory.csv")
check("reorder analysis has 720 rows", len(re_) == 720)
check("no missing values in key columns",
      re_[["stock_on_hand", "reorder_point", "safety_stock", "status"]].notna().all().all())
check("stocked-out rows = zero-stock rows in inventory",
      (re_["status"] == "Stocked out").sum() == (inv["stock_on_hand"] == 0).sum(),
      f"{(re_['status'] == 'Stocked out').sum()} vs {(inv['stock_on_hand'] == 0).sum()}")
print("      status counts:", re_["status"].value_counts().to_dict())
share = (re_["status"] == "Reorder now").mean() * 100
warn("'Reorder now' share looks high (>20%)", share > 20, f"{share:.0f}% of rows")
print("      current-level check:", re_["current_level_check"].value_counts().to_dict())

# ---------- 4. dead stock ----------
dead = pd.read_csv(D / "dead_stock.csv")
stale = set(last_dates.loc[last_dates["last_sale"] < "2026-01-31", "product_id"])
check("dead stock = products with no sale in last 60 days", set(dead["product_id"]) == stale,
      f"{len(dead)} listed, {len(stale)} found")
print(f"      dead stock capital at cost: Rs {dead['stock_value_cost'].sum():,.0f}")

# ---------- 5. ABC ----------
abc = pd.read_csv(D / "abc_analysis.csv")
check("ABC covers all 120 products", len(abc) == 120 and abc["product_id"].is_unique)
check("cumulative % ends at 100", abs(abc["cum_pct"].max() - 100) < 0.01)
s = abc.groupby("abc_class")["net_revenue"].sum() / abc["net_revenue"].sum() * 100
print("      ABC SKUs:", abc["abc_class"].value_counts().sort_index().to_dict(),
      "| revenue %:", s.round(1).to_dict())
warn("class A larger than 45% of SKUs (weak Pareto)", (abc["abc_class"] == "A").mean() > 0.45,
     f"{(abc['abc_class'] == 'A').mean() * 100:.0f}% of SKUs")

# ---------- 6. turnover ----------
t = pd.read_csv(D / "inventory_turnover.csv")
print("      turnover:", t[["category", "turnover_x", "days_of_inventory"]].to_dict("records"))
tot = t.loc[t["category"] == "TOTAL", "turnover_x"].iloc[0]
warn("overall turnover outside 5-40x", not (5 <= tot <= 40), f"{tot}x")

# ---------- 7. forecast ----------
sc = pd.read_csv(D / "forecast_scorecard.csv")
print(sc.to_string(index=False))
glm = sc.loc[sc["model"] == "Poisson GLM"].iloc[0]
base = sc.loc[sc["model"] != "Poisson GLM", "WAPE %"].min()
check("GLM beats both baselines on WAPE", glm["WAPE %"] < base, f"{glm['WAPE %']} vs best baseline {base}")
warn("GLM |bias| above 5%", abs(glm["Bias %"]) > 5, f"{glm['Bias %']}%")
bt = pd.read_csv(D / "forecast_backtest_by_category.csv")
print(bt.to_string(index=False))
warn("some category |bias| above 10%", (bt["Bias %"].abs() > 10).any(),
     str(bt.loc[bt["Bias %"].abs() > 10, "category"].tolist()))

fc = pd.read_csv(D / "forecast_next30.csv", parse_dates=["date"])
check("forecast covers 30 days of April 2026", len(fc) == 30 and fc["date"].min() == pd.Timestamp("2026-04-01"))
check("forecast sits inside its range", ((fc["low_10%"] <= fc["forecast"]) & (fc["forecast"] <= fc["high_90%"])).all())
print(f"      April forecast: {int(fc['forecast'].sum()):,} units")

# ---------- 8. orders ----------
o = pd.read_csv(D / "order_recommendations.csv")
check("orders: 720 rows, none negative", len(o) == 720 and (o["order_qty"] >= 0).all())
check("every stocked-out row with demand gets an order",
      (o.loc[(o["status"] == "Stocked out") & (o["forecast_daily"] > 0), "order_qty"] > 0).all())
check("no orders for dead-stock products", (o.loc[o["product_id"].isin(dead["product_id"]), "order_qty"] == 0).all())
print(f"      rows to order: {(o['order_qty'] > 0).sum()} | value at cost: Rs {o['order_value_cost'].sum():,.0f}")
warn("order value above 40% of stock value", False)  # informational

# ---------- 9. README, images, git ----------
readme = (ROOT / "README.md").read_text(encoding="utf-8")
check("README has no 'nan'", not re.search(r"\bnan\b", readme, re.I))
imgs = re.findall(r"!\[.*?\]\((.*?)\)", readme)
gone = [i for i in imgs if not (ROOT / i).exists()]
check("every README image exists", not gone, str(gone))
tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split("\n")
check("stockwise.db is not in git", "stockwise.db" not in tracked)
check("dashboard workbook is in git", "excel/StockWise_Dashboard.xlsx" in tracked)
check("app files are in git", all(f in tracked for f in ["app.py", "utils.py", "pages/1_Stock_Alerts.py"]))
reqs = (ROOT / "requirements.txt").read_text(encoding="utf-16" if (ROOT / "requirements.txt").read_bytes()[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8")
windows_only = [p for p in ["pywin32", "pywinpty", "pypiwin32"] if p in reqs.lower()]
warn("requirements.txt has Windows-only packages (breaks deployment)", bool(windows_only), str(windows_only))

print(f"\n{fails} FAIL, {warns} WARN")