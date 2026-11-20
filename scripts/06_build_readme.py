"""StockWise - Step 6: build README.md from the database and the saved analysis files.
Every number in the README is computed here, so nothing is typed by hand."""
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data"

needed = ["abc_analysis.csv", "dead_stock.csv", "reorder_analysis.csv", "inventory_turnover.csv",
          "forecast_next30.csv", "category_uplift.csv", "order_recommendations.csv",
          "forecast_scorecard.csv", "forecast_backtest_by_category.csv"]
missing = [f for f in needed if not (D / f).exists()]
assert not missing, f"Missing files (re-run the notebooks): {missing}"


def inr(x):
    """Indian digit grouping: 12,34,567"""
    x = int(round(x))
    s = str(abs(x))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts + [tail])
    return ("-" if x < 0 else "") + "Rs " + s


def md(df, index=False):
    if index:
        df = df.reset_index()
    cols = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for row in df.itertuples(index=False):
        lines.append("| " + " | ".join(str(v) for v in row) + " |")
    return "\n".join(lines)


# ---------- numbers from the database ----------
con = sqlite3.connect(ROOT / "stockwise.db")
q = lambda sql: con.execute(sql).fetchone()
rows, invoices, units, d0, d1 = q("SELECT COUNT(*), COUNT(DISTINCT invoice_id), SUM(qty), MIN(sale_date), MAX(sale_date) FROM sales")
gross, net, profit = q("SELECT SUM(gross_sales), SUM(net_revenue), SUM(gross_profit) FROM sales_enriched")
fy = dict(con.execute("SELECT fy, SUM(net_revenue) FROM sales_enriched GROUP BY fy").fetchall())
n_prod, n_store, n_sup = q("SELECT (SELECT COUNT(*) FROM products), (SELECT COUNT(*) FROM stores), (SELECT COUNT(*) FROM suppliers)")
con.close()
growth = (fy["2025-26"] / fy["2024-25"] - 1) * 100

# ---------- numbers from the analysis files ----------
abc = pd.read_csv(D / "abc_analysis.csv")
abc_s = abc.groupby("abc_class").agg(SKUs=("product_id", "count"), rev=("net_revenue", "sum"))
abc_s["% of SKUs"] = (abc_s["SKUs"] / abc_s["SKUs"].sum() * 100).round(1)
abc_s["% of revenue"] = (abc_s["rev"] / abc_s["rev"].sum() * 100).round(1)
abc_s = abc_s.drop(columns="rev")

dead = pd.read_csv(D / "dead_stock.csv")
re_ = pd.read_csv(D / "reorder_analysis.csv")
status = re_["status"].value_counts().rename("rows").to_frame()
check = re_["current_level_check"].value_counts().rename("rows").to_frame()
at_risk = re_["daily_revenue_at_risk"].sum()
n_out = int((re_["status"] == "Stocked out").sum())
n_reorder = int((re_["status"] == "Reorder now").sum())

turn = pd.read_csv(D / "inventory_turnover.csv")
turn_tbl = turn[["category", "turnover_x", "days_of_inventory"]].copy()
total_turn = turn.loc[turn["category"] == "TOTAL", "turnover_x"].iloc[0]

score = pd.read_csv(D / "forecast_scorecard.csv").sort_values("WAPE %")
bt = pd.read_csv(D / "forecast_backtest_by_category.csv")
fc = pd.read_csv(D / "forecast_next30.csv")
upl = pd.read_csv(D / "category_uplift.csv")
orders = pd.read_csv(D / "order_recommendations.csv")
n_orders = int((orders["order_qty"] > 0).sum())
order_val = orders["order_value_cost"].sum()
best = score.iloc[0]

readme = f"""# StockWise: Inventory & Sales Intelligence (India)

An end-to-end retail analytics and demand-forecasting project built with **Python, SQL and Excel**.
It answers three business questions for an Indian retail chain: **what sells, what is about to run out, and what is sitting idle.**
It then forecasts demand and turns the forecast into reorder recommendations.

> **Data is synthetic.** Brands, suppliers and stores are fictional. GST rates are illustrative, so check the current official rate for every product before real use.
> The column structure follows a typical Indian retail export, so a company can load its own CSVs with the same columns.

![Dashboard](images/dashboard.png)

## Dataset

| Item | Value |
|---|---|
| Period | {d0} to {d1} (FY 2024-25 and FY 2025-26, April to March) |
| Sales lines | {rows:,} across {invoices:,} invoices |
| Stores / products / suppliers | {n_store} / {n_prod} / {n_sup} |
| Stores | Pune, Mumbai, Delhi, Bengaluru, Hyderabad, Chennai |
| Inventory | Snapshot of stock per store and product on {d1} |
| Currency | Indian rupees. MRP and selling price include GST |

**Indian retail conventions used:** MRP is the price ceiling and includes GST, so net revenue is `selling_price / (1 + GST%)`. Margins and ABC ranking use net revenue. The financial year runs April to March. UPI is the most common payment mode. Festival demand spikes (Diwali, Holi, Eid) and a summer beverage peak are built into the data.

## Key results

| Metric | Value |
|---|---|
| Net revenue (excl. GST) | {inr(net)} |
| Gross sales (incl. GST) | {inr(gross)} |
| Gross profit | {inr(profit)} ({profit / net * 100:.1f}% margin) |
| Units sold | {int(units):,} |
| FY 2025-26 vs FY 2024-25 net revenue | {growth:+.1f}% |
| Store-product rows stocked out | {n_out} of {len(re_)} |
| Rows flagged "Reorder now" | {n_reorder} of {len(re_)} |
| Net revenue lost per day from stocked-out rows | {inr(at_risk)} |
| Dead-stock products | {len(dead)}, with {inr(dead['stock_value_cost'].sum())} of capital locked (at cost) |
| Inventory turnover (overall, approximate) | {total_turn}x per year |

### ABC analysis (FY 2025-26, by net revenue)
{md(abc_s, index=True)}

![ABC Pareto](images/05_abc_pareto.png)

### Reorder status (95% service level)
{md(status, index=True)}

### How the current reorder levels compare with calculated reorder points
{md(check, index=True)}

### Dead stock (no sale anywhere for 60+ days)
{md(dead[["product_id", "sku_name", "category", "days_since_last_sale", "units_in_stock", "stock_value_cost"]])}

### Inventory turnover by category
{md(turn_tbl)}

## Demand forecasting

Models were tested on the final 90 days (Jan to Mar 2026), trained only on earlier data (a time split, never random). The 8 dead-stock products were excluded because their demand stopped for a stock reason, not a demand pattern.

{md(score.round(2))}

WAPE = total absolute error / total actual units. Bias below zero means under-forecasting. The Poisson GLM uses weekday, yearly trend, a summer flag and festival flags. The best model by WAPE is **{best.iloc[0]}** at {best['WAPE %']}%.

![Forecast vs actual](images/07_glm_forecast.png)

**Per-category backtest** (one model per category):
{md(bt)}

**30-day forecast (April 2026), all stores:** about **{int(fc['forecast'].sum()):,} units**, with an 80% range per day in `data/forecast_next30.csv`.

![April forecast](images/08_forecast_april2026.png)

### From forecast to orders
Each category's April uplift (forecast April average / actual Jan-Mar average) scales every store-product's recent demand:

{md(upl)}

Target stock = forecast daily demand x (lead time + 7-day review period) + safety stock. Order quantity = target stock - stock on hand, never below zero.
Result: **{n_orders} of {len(orders)} store-product rows** get an order, with a total order value of **{inr(order_val)}** at cost (`data/order_recommendations.csv`).

## Excel dashboard
Pivot tables, KPI cards, charts and slicers (financial year, region, category) built in `excel/StockWise_Dashboard.xlsx`. A conditional-formatted **Reorder_Alert** sheet shows stocked-out and reorder-now rows sorted by revenue at risk. All dashboard totals were reconciled against SQL.

![Reorder alert](images/reorder_alert.png)

## Project structure
StockWise/
├── data/ generated CSVs and analysis outputs
├── sql/ schema.sql, validation.sql, analysis_queries.sql
├── scripts/ 01-06: generate data, load database, export Excel, build README
├── notebooks/ 01_cleaning_eda, 02_analytics, 03_forecasting
├── excel/ StockWise_Dashboard.xlsx
├── images/ charts and screenshots
└── README.md


## How to run
```bash
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
python scripts/01_generate_master_data.py
python scripts/02_generate_sales.py
python scripts/03_generate_inventory.py
python scripts/04_load_database.py
python scripts/run_sql.py sql/validation.sql
```
Then run the three notebooks in order, then `python scripts/05_export_excel.py` and `python scripts/06_build_readme.py`.

## To use it with a real company's data
Replace the CSVs in `data/` (suppliers, stores, products, sales, inventory) with exports in the same columns, keep the real GST rate per product, and replace the festival windows in the forecasting notebook with the company's own calendar. Then re-run the pipeline.

## Assumptions and limitations
- **Synthetic data.** Patterns were planted (festivals, summer beverages, weekday effect, 8 dead-stock products), and the analysis recovers them. Real data will be messier.
- **Festival flags use the same windows used to generate the data**, so the forecast test is more flattering than real data would give. Only Diwali, Holi and Eid are modelled, and each is learned from one or two occurrences.
- **Category margin differences are random noise** from the data generator and are not a finding.
- **Inventory turnover is approximate**: it uses one stock snapshot, not average inventory over the year.
- **Safety stock formula** assumes fixed lead time and independent daily demand. Z = 1.645 targets a 95% service level. The 90-day window includes the Holi/Eid spike, so reorder points and the "Reorder now" count are somewhat high.
- The "too low / too high" thresholds for current reorder levels (below 80% or above 125% of the calculated point) are a judgment call.
- The forecast range reflects day-to-day randomness only, not uncertainty in the fitted coefficients. The yearly trend is extrapolated.
- Order recommendations ignore supplier minimum order quantities and pack sizes, and use an assumed 7-day review period. They are for a manager to review, not automatic purchasing.
- `invoice_id` grouping is synthetic.

## Tools
Python (pandas, NumPy, statsmodels, matplotlib), SQL (SQLite, CTEs, window functions, views), Excel (PivotTables, slicers, conditional formatting), Git/GitHub.
"""

(ROOT / "README.md").write_text(readme, encoding="utf-8")
print("README.md written\n")
print("RESUME BULLETS (computed from your data):")
print(f"- Built an end-to-end inventory and sales analytics system in Python, SQL and Excel on {rows:,} transactions "
      f"across {n_store} stores and {n_prod} products ({inr(net)} net revenue, two Indian financial years).")
print(f"- Identified {n_out} stocked-out and {n_reorder} below-reorder-point store-product rows, {len(dead)} dead-stock "
      f"products ({inr(dead['stock_value_cost'].sum())} locked capital) using ABC analysis, safety-stock reorder points and turnover.")
print(f"- Developed a Poisson GLM demand forecast (WAPE {best['WAPE %']}% on a held-out 90-day test, vs baselines) and converted "
      f"it into category-level order recommendations for {n_orders} store-product rows.")