from pathlib import Path

import pandas as pd
import streamlit as st

from utils import inr

ROOT = Path(__file__).resolve().parent.parent
st.set_page_config(page_title="Order Recommendations", page_icon="🛒", layout="wide")


@st.cache_data
def load():
    return pd.read_csv(ROOT / "data" / "order_recommendations.csv")


o = load()
st.title("Order recommendations")
st.caption("Target stock = forecast daily demand x (lead time + 7-day review period) + safety stock. "
           "Order = target - stock on hand, never below zero. A list for a manager to review, not automatic purchasing.")

st.sidebar.header("Filters")
city = st.sidebar.multiselect("City", sorted(o["city"].unique()), default=sorted(o["city"].unique()))
category = st.sidebar.multiselect("Category", sorted(o["category"].unique()), default=sorted(o["category"].unique()))
status = st.sidebar.multiselect("Status", sorted(o["status"].unique()), default=sorted(o["status"].unique()))

f = o[o["city"].isin(city) & o["category"].isin(category) & o["status"].isin(status)]
to_order = f[f["order_qty"] > 0]
if to_order.empty:
    st.warning("No orders for this selection.")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Rows to order", f"{len(to_order)} of {len(f)}")
c2.metric("Units to order", f"{int(to_order['order_qty'].sum()):,}")
c3.metric("Order value (at cost)", inr(to_order["order_value_cost"].sum()))

st.subheader("Order value by category (Rs)")
st.bar_chart(to_order.groupby("category")["order_value_cost"].sum().sort_values(), horizontal=True)

st.subheader("Largest orders first")
st.dataframe(to_order.sort_values("order_value_cost", ascending=False)[
    ["city", "sku_name", "category", "status", "stock_on_hand", "forecast_daily",
     "reorder_point", "target_stock", "order_qty", "order_value_cost"]], hide_index=True)
st.download_button("Download order list (CSV)", to_order.to_csv(index=False), "orders.csv", "text/csv")
st.info("Not modelled: supplier minimum order quantities, pack sizes and budgets. The 7-day review period is an assumption.")