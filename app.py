from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="StockWise", page_icon="📦", layout="wide")


@st.cache_data
def load_sales():
    return pd.read_csv(ROOT / "data" / "app_sales_monthly.csv")


sales = load_sales()

st.title("StockWise: Inventory & Sales Intelligence (India)")
st.caption("Synthetic data. Figures exclude GST. Financial year runs April to March.")

# ---------- sidebar filters ----------
st.sidebar.header("Filters")
fy = st.sidebar.multiselect("Financial year", sorted(sales["fy"].unique()), default=sorted(sales["fy"].unique()))
region = st.sidebar.multiselect("Region", sorted(sales["region"].unique()), default=sorted(sales["region"].unique()))
category = st.sidebar.multiselect("Category", sorted(sales["category"].unique()), default=sorted(sales["category"].unique()))

f = sales[sales["fy"].isin(fy) & sales["region"].isin(region) & sales["category"].isin(category)]
if f.empty:
    st.warning("No data for this selection. Pick at least one option in each filter.")
    st.stop()

# ---------- KPI cards ----------
net = f["net_revenue"].sum()
c1, c2, c3 = st.columns(3)
c1.metric("Net revenue", f"Rs {net / 1e7:.2f} Cr")
c2.metric("Units sold", f"{int(f['units'].sum()):,}")
c3.metric("Gross margin", f"{f['gross_profit'].sum() / net * 100:.1f}%")

# ---------- charts ----------
st.subheader("Monthly net revenue (Rs lakh)")
monthly = f.groupby("month")["net_revenue"].sum() / 1e5
st.line_chart(monthly)

left, right = st.columns(2)
with left:
    st.subheader("Net revenue by category (Rs lakh)")
    st.bar_chart(f.groupby("category")["net_revenue"].sum().sort_values() / 1e5, horizontal=True)
with right:
    st.subheader("Net revenue by city (Rs lakh)")
    st.bar_chart(f.groupby("city")["net_revenue"].sum().sort_values() / 1e5, horizontal=True)