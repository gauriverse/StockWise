
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
rng = np.random.default_rng(42)  # fixed seed -> reproducible

products = pd.read_csv(DATA_DIR / "products.csv")
stores = pd.read_csv(DATA_DIR / "stores.csv")

dates = pd.date_range("2024-04-01", "2026-03-31", freq="D")
D, S, P = len(dates), len(stores), len(products)

# ---------- 1. Base daily demand per product ----------
cat_base = {"Staples & Grains": 0.9, "Dairy": 1.6, "Snacks": 1.4, "Beverages": 1.2,
            "Personal Care": 0.6, "Household": 0.6, "Packaged Foods": 0.7, "Stationery": 0.4}
price_factor = np.clip((150 / products["mrp"].values) ** 0.35, 0.5, 2.0)  # cheaper items sell more
popularity = rng.lognormal(mean=0, sigma=0.8, size=P)                     # few hits, many slow movers
base = products["category"].map(cat_base).values * price_factor * popularity

# ---------- 2. Store, weekday and growth factors ----------
store_factor = stores["city"].map({"Mumbai": 1.3, "Delhi": 1.2, "Bengaluru": 1.1,
                                   "Pune": 1.0, "Hyderabad": 0.95, "Chennai": 0.9}).values
weekday_factor = np.array([0.9, 0.9, 0.95, 0.95, 1.1, 1.3, 1.25])[dates.dayofweek]  # Mon..Sun
trend = 1 + 0.10 * (np.arange(D) / 365)  # ~10% yearly growth

# ---------- 3. Seasonality (dates x products) ----------
season = np.ones((D, P))
month_rules = {
    "Beverages":  {3: 1.2, 4: 1.5, 5: 1.5, 6: 1.4, 12: 0.8, 1: 0.8},
    "Stationery": {4: 1.8, 5: 1.8, 6: 1.8, 7: 1.3, 8: 0.8, 9: 0.8, 10: 0.8,
                   11: 0.8, 12: 0.8, 1: 0.8, 2: 0.8, 3: 0.8},
}
for cat, rules in month_rules.items():
    cat_mask = (products["category"] == cat).values
    for month, mult in rules.items():
        season[np.ix_(dates.month == month, cat_mask)] = mult

# ---------- 4. Festival windows (approximate) ----------
diwali = {"Snacks": 1.8, "Packaged Foods": 1.7, "Dairy": 1.4, "Household": 1.5,
          "Staples & Grains": 1.3, "Personal Care": 1.3}
holi = {"Snacks": 1.6, "Beverages": 1.5, "Dairy": 1.4, "Packaged Foods": 1.3}
eid = {"Dairy": 1.4, "Staples & Grains": 1.3, "Packaged Foods": 1.4, "Snacks": 1.2}
festivals = [
    ("2024-04-01", "2024-04-11", eid),
    ("2024-10-22", "2024-11-02", diwali),
    ("2025-02-26", "2025-03-14", holi),   # Holi 2025 window
    ("2025-03-24", "2025-03-31", eid),
    ("2025-10-10", "2025-10-21", diwali),
    ("2026-02-24", "2026-03-04", holi),   # Holi 2026 window
    ("2026-03-13", "2026-03-21", eid),
]
is_festival = np.zeros(D, dtype=bool)
for start, end, boosts in festivals:
    in_window = (dates >= start) & (dates <= end)
    is_festival |= in_window
    for cat, mult in boosts.items():
        cat_mask = (products["category"] == cat).values
        season[np.ix_(in_window, cat_mask)] *= mult

# ---------- 5. Dead stock: 8 products stop selling after 31 Dec 2025 ----------
eligible = products.index[products["shelf_life_days"].isna() | (products["shelf_life_days"] >= 180)]
dead_idx = np.sort(rng.choice(eligible, size=8, replace=False))
stopped = np.where(dates > "2025-12-31")[0]
# ---------- 6. Expected demand and random draw ----------
lam = (base[None, None, :] * store_factor[None, :, None] * weekday_factor[:, None, None]
       * trend[:, None, None] * season[:, None, :])
lam[np.ix_(stopped, np.arange(S), dead_idx)] = 0
qty = rng.poisson(lam)  # shape (days, stores, products)

d, s, p = np.nonzero(qty)
df = pd.DataFrame({
    "sale_date": dates[d],
    "store_id": stores["store_id"].values[s],
    "product_id": products["product_id"].values[p],
    "qty": qty[d, s, p],
})

# ---------- 7. Discounts and selling price ----------
p_disc = np.where(is_festival[d], 0.35, 0.12)  # more discounts in festival windows
has_disc = rng.random(len(df)) < p_disc
df["discount_pct"] = rng.choice([2, 5, 10], size=len(df)) * has_disc
df["selling_price"] = (products["mrp"].values[p] * (1 - df["discount_pct"] / 100)).round(2)

# ---------- 8. Invoices (synthetic grouping) and payment mode ----------
lines_in_day = df.groupby(["store_id", "sale_date"])["qty"].transform("size")
n_baskets = (lines_in_day // 4).clip(lower=1)
basket = (rng.random(len(df)) * n_baskets).astype(int) + 1
df["invoice_id"] = ("INV-" + df["store_id"] + "-" + df["sale_date"].dt.strftime("%Y%m%d")
                    + "-" + basket.astype(str).str.zfill(3))
inv = pd.DataFrame({"invoice_id": df["invoice_id"].unique()})
inv["payment_mode"] = rng.choice(["UPI", "Card", "Cash"], size=len(inv), p=[0.55, 0.25, 0.20])
df = df.merge(inv, on="invoice_id")

df = df[["invoice_id", "sale_date", "store_id", "product_id", "qty",
         "selling_price", "discount_pct", "payment_mode"]].sort_values(
         ["sale_date", "invoice_id"]).reset_index(drop=True)

# ---------- 9. Sanity checks ----------
chk = df.merge(products[["product_id", "mrp", "gst_rate", "unit_cost"]], on="product_id")
assert (df["qty"] > 0).all(), "Non-positive quantity"
assert (chk["selling_price"] <= chk["mrp"]).all(), "Selling price above MRP"
assert (chk["selling_price"] / (1 + chk["gst_rate"] / 100) > chk["unit_cost"]).all(), "Sold below cost"
assert df["store_id"].isin(stores["store_id"]).all()

df.to_csv(DATA_DIR / "sales.csv", index=False)

# ---------- 10. Report ----------
chk["gross"] = chk["qty"] * chk["selling_price"]
print(f"rows: {len(df):,} | invoices: {df['invoice_id'].nunique():,}")
print(f"dates: {df['sale_date'].min().date()} to {df['sale_date'].max().date()}")
print(f"total gross sales (GST-inclusive): Rs {chk['gross'].sum():,.0f}")
print("\nrows per store:\n", df["store_id"].value_counts().sort_index())
print("\nANSWER KEY - products planted as dead stock (don't share this):")
print(products.loc[dead_idx, ["product_id", "sku_name"]].to_string(index=False))