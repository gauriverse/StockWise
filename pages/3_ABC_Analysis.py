from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
st.set_page_config(page_title="ABC Analysis", page_icon="🔠", layout="wide")


@st.cache_data
def load():
    return pd.read_csv(ROOT / "data" / "abc_analysis.csv")


a = load()
st.title("ABC analysis (FY 2025-26)")
st.caption("A = first 80% of net revenue, B = next 15%, C = last 5%. A product is classed by where it starts on the cumulative curve.")

s = a.groupby("abc_class").agg(SKUs=("product_id", "count"), revenue=("net_revenue", "sum"))
s["% of SKUs"] = (s["SKUs"] / s["SKUs"].sum() * 100).round(1)
s["% of revenue"] = (s["revenue"] / s["revenue"].sum() * 100).round(1)

cols = st.columns(3)
for col, cls in zip(cols, ["A", "B", "C"]):
    if cls in s.index:
        col.metric(f"Class {cls}", f"{int(s.loc[cls, 'SKUs'])} SKUs",
                   f"{s.loc[cls, '% of revenue']}% of revenue", delta_color="off")

st.subheader("Cumulative share of revenue (products ranked high to low)")
st.line_chart(a.reset_index(drop=True)["cum_pct"])

pick = st.multiselect("Class", ["A", "B", "C"], default=["A", "B", "C"])
view = a[a["abc_class"].isin(pick)]
st.dataframe(view[["abc_class", "product_id", "sku_name", "category", "net_revenue", "pct", "cum_pct"]].round(2),
             hide_index=True)