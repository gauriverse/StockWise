from pathlib import Path

import pandas as pd
import streamlit as st

from utils import inr

ROOT = Path(__file__).resolve().parent.parent
st.set_page_config(page_title="Stock Alerts", page_icon="🚨", layout="wide")


@st.cache_data
def load():
    return pd.read_csv(ROOT / "data" / "reorder_analysis.csv")


r = load()
st.title("Stock alerts")
st.caption("Reorder points use a 95% service level (safety stock = 1.645 x demand std x sqrt(lead time)). Synthetic data.")

st.sidebar.header("Filters")
city = st.sidebar.multiselect("City", sorted(r["city"].unique()), default=sorted(r["city"].unique()))
category = st.sidebar.multiselect("Category", sorted(r["category"].unique()), default=sorted(r["category"].unique()))
show = st.sidebar.multiselect("Show status", ["Stocked out", "Reorder now"], default=["Stocked out", "Reorder now"])

f = r[r["city"].isin(city) & r["category"].isin(category)]
if f.empty:
    st.warning("No data for this selection. Pick at least one option in each filter.")
    st.stop()

# KPI cards count every row in the selected cities and categories
c1, c2, c3, c4 = st.columns(4)
c1.metric("Stocked out", int((f["status"] == "Stocked out").sum()))
c2.metric("Reorder now", int((f["status"] == "Reorder now").sum()))
c3.metric("Cover shorter than lead time", int((f["days_of_cover"] < f["avg_lead_time_days"]).sum()))
c4.metric("Revenue lost per day (stockouts)", inr(f["daily_revenue_at_risk"].sum()))

alerts = (f[f["status"].isin(show)]
          .sort_values(["daily_revenue_at_risk", "days_of_cover"], ascending=[False, True]))
st.subheader(f"{len(alerts)} rows need attention")
st.dataframe(
    alerts[["city", "sku_name", "category", "status", "stock_on_hand", "reorder_level",
            "reorder_point", "days_of_cover", "avg_lead_time_days", "daily_revenue_at_risk"]],
    hide_index=True)
st.download_button("Download this list (CSV)", alerts.to_csv(index=False), "stock_alerts.csv", "text/csv")

st.subheader("Alerts by category")
st.bar_chart(alerts.groupby("category").size().sort_values(), horizontal=True)

st.subheader("Is the current reorder level right?")
st.caption("Compared with the calculated reorder point. Too low = below 80%, too high = above 125% (a judgment call).")
st.bar_chart(f["current_level_check"].value_counts())