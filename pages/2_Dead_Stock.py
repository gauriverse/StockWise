from pathlib import Path

import pandas as pd
import streamlit as st

from utils import inr

ROOT = Path(__file__).resolve().parent.parent
st.set_page_config(page_title="Dead Stock", page_icon="🧊", layout="wide")


@st.cache_data
def load():
    return pd.read_csv(ROOT / "data" / "dead_stock.csv")


d = load()
st.title("Dead stock")
st.caption("Products with no sale anywhere for 60+ days that still hold stock. Valued at cost (what the business paid).")

c1, c2, c3 = st.columns(3)
c1.metric("Dead-stock products", len(d))
c2.metric("Capital locked (at cost)", inr(d["stock_value_cost"].sum()))
c3.metric("Longest without a sale", f"{int(d['days_since_last_sale'].max())} days")

st.subheader("Capital locked by product (Rs)")
st.bar_chart(d.set_index("sku_name")["stock_value_cost"].sort_values(), horizontal=True)

st.dataframe(d[["product_id", "sku_name", "category", "last_sale_date", "days_since_last_sale",
                "units_in_stock", "stock_value_cost"]], hide_index=True)
st.info("Suggested actions: discount or bundle these items, return to supplier if allowed, and stop reordering.")