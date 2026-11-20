from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
st.set_page_config(page_title="Demand Forecast", page_icon="📈", layout="wide")


@st.cache_data
def load():
    d = ROOT / "data"
    return (pd.read_csv(d / "app_daily_units.csv", parse_dates=["sale_date"]),
            pd.read_csv(d / "forecast_next30.csv", parse_dates=["date"]),
            pd.read_csv(d / "forecast_scorecard.csv"),
            pd.read_csv(d / "forecast_backtest_by_category.csv"),
            pd.read_csv(d / "category_uplift.csv"))


daily, fc, score, bt, upl = load()
st.title("Demand forecast")
st.caption("Poisson GLM with weekday, yearly trend, summer and festival (Diwali, Holi, Eid) effects. "
           "Chain-wide units per day, excluding the 8 dead-stock products. Synthetic data.")

c1, c2, c3 = st.columns(3)
c1.metric("April 2026 forecast", f"{int(fc['forecast'].sum()):,} units")
c2.metric("Average per day", f"{fc['forecast'].mean():,.0f} units")
best = score.sort_values("WAPE %").iloc[0]
c3.metric("Best model (test WAPE)", f"{best['WAPE %']}%", best["model"], delta_color="off")

st.subheader("Recent actual sales and 30-day forecast (units/day)")
hist = daily[daily["sale_date"] >= "2026-02-01"].set_index("sale_date")["units"].rename("Actual")
chart = pd.concat([hist,
                   fc.set_index("date")["forecast"].rename("Forecast"),
                   fc.set_index("date")["low_10%"].rename("Low (10%)"),
                   fc.set_index("date")["high_90%"].rename("High (90%)")], axis=1)
st.line_chart(chart)
st.caption("The range covers day-to-day randomness only, not uncertainty in the fitted model. "
           "No festival falls in April in our calendar, so none is assumed.")

left, right = st.columns(2)
with left:
    st.subheader("Model comparison (last 90 days held out)")
    st.dataframe(score.sort_values("WAPE %"), hide_index=True)
    st.caption("WAPE = total absolute error / total actual units. Bias below 0 means under-forecasting.")
with right:
    st.subheader("April uplift by category")
    st.dataframe(upl, hide_index=True)
    st.caption("Uplift = forecast April daily average / actual Jan-Mar daily average.")

st.subheader("Per-category backtest")
st.dataframe(bt, hide_index=True)

st.download_button("Download 30-day forecast (CSV)", fc.to_csv(index=False), "forecast_april2026.csv", "text/csv")