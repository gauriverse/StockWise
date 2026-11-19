
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
rng = np.random.default_rng(7)
SNAP = pd.Timestamp("2026-03-31")

products = pd.read_csv(DATA_DIR / "products.csv")
stores = pd.read_csv(DATA_DIR / "stores.csv")
suppliers = pd.read_csv(DATA_DIR / "suppliers.csv")
sales = pd.read_csv(DATA_DIR / "sales.csv", parse_dates=["sale_date"])

# ---------- 1. Demand reference windows ----------
last90 = sales[sales["sale_date"] >= SNAP - pd.Timedelta(days=89)]            # 1 Jan - 31 Mar 2026 (90 days)
refwin = sales[(sales["sale_date"] >= "2025-10-01") & (sales["sale_date"] <= "2025-12-31")]  # 92 days

# dead stock = sold in Oct-Dec 2025 but not at all after 31 Dec 2025
sold_after = set(sales.loc[sales["sale_date"] > "2025-12-31", "product_id"])
sold_before = set(refwin["product_id"])
dead_ids = sorted(sold_before - sold_after)
assert len(dead_ids) == 8, f"Expected 8 dead-stock products, found {len(dead_ids)}"

grid = pd.MultiIndex.from_product([stores["store_id"], products["product_id"]],
                                  names=["store_id", "product_id"])
recent = (last90.groupby(["store_id", "product_id"])["qty"].sum() / 90).reindex(grid, fill_value=0)
ref = (refwin.groupby(["store_id", "product_id"])["qty"].sum() / 92).reindex(grid, fill_value=0)

inv = pd.DataFrame({"recent_daily": recent, "ref_daily": ref}).reset_index()
inv = (inv.merge(products[["product_id", "supplier_id", "shelf_life_days", "unit_cost"]], on="product_id")
          .merge(suppliers[["supplier_id", "avg_lead_time_days"]], on="supplier_id"))
n = len(inv)

# ---------- 2. Reorder level (manager's rough rule) ----------
is_dead = inv["product_id"].isin(dead_ids).values
demand = np.where(is_dead, inv["ref_daily"].values, inv["recent_daily"].values)
lead = inv["avg_lead_time_days"].values
shelf = inv["shelf_life_days"].fillna(10**6).values
reorder = np.maximum(2, np.ceil(demand * lead * rng.uniform(0.7, 1.5, n))).astype(int)

# ---------- 3. Stock situation per row ----------
scenario = rng.choice(["stockout", "low", "normal", "overstock"], size=n, p=[0.04, 0.12, 0.68, 0.16])
scenario = np.where(is_dead, "dead", scenario)
scenario = np.where((shelf < 30) & (scenario == "overstock"), "normal", scenario)  # perishables can't be overstocked

stock = np.zeros(n)
m = scenario == "low"
stock[m] = np.maximum(1, np.floor(reorder * rng.uniform(0.1, 0.95, n)))[m]
m = scenario == "normal"
stock[m] = np.maximum(np.round(demand * rng.uniform(lead + 3, lead + 20)), reorder + 1)[m]
m = scenario == "overstock"
stock[m] = np.maximum(np.round(demand * rng.uniform(60, 150, n)), reorder * 3)[m]
m = scenario == "dead"
stock[m] = np.maximum(np.round(demand * rng.uniform(30, 90, n)), reorder + 1)[m]

# shelf-life cap (never hold more than 80% of shelf life in stock)
cap = np.maximum(np.floor(0.8 * shelf * demand), reorder + 1)
capped = np.isin(scenario, ["normal", "overstock"])
stock = np.where(capped, np.minimum(stock, cap), stock).astype(int)

# ---------- 4. Last restock date ----------
low_d = np.select([scenario == "normal", scenario == "overstock", scenario == "dead"], [1, 3, 90], default=7)
high_d = np.select([scenario == "normal", scenario == "overstock", scenario == "dead"],
                   [lead * 2 + 2, 31, 151], default=36)
days_ago = rng.integers(low_d, high_d)
inv["last_restock_date"] = (SNAP - pd.to_timedelta(days_ago, unit="D")).strftime("%Y-%m-%d")

inv["stock_on_hand"] = stock
inv["reorder_level"] = reorder
inv["snapshot_date"] = SNAP.strftime("%Y-%m-%d")

out = inv[["store_id", "product_id", "stock_on_hand", "reorder_level",
           "last_restock_date", "snapshot_date"]]

# ---------- 5. Sanity checks ----------
assert len(out) == len(stores) * len(products)
assert not out.duplicated(["store_id", "product_id"]).any()
assert (out["stock_on_hand"] >= 0).all() and (out["reorder_level"] >= 2).all()
assert (pd.to_datetime(out["last_restock_date"]) <= SNAP).all()

out.to_csv(DATA_DIR / "inventory.csv", index=False)

# ---------- 6. Report ----------
value = inv["stock_on_hand"] * inv["unit_cost"]
print(f"rows: {len(out)} | total stock value at cost: Rs {value.sum():,.0f}")
print("rows at/below reorder level:", int((out["stock_on_hand"] <= out["reorder_level"]).sum()))
print("rows with zero stock:", int((out["stock_on_hand"] == 0).sum()))
print("\nANSWER KEY - dead-stock products found in sales (compare with your Step 4 list):")
print(products.loc[products["product_id"].isin(dead_ids), ["product_id", "sku_name"]].to_string(index=False))
print(f"dead stock value at cost: Rs {value[is_dead].sum():,.0f}")