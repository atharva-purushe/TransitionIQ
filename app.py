from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data import load_assumptions, load_personas, load_portfolios
from src.engine import analyze

ROOT = Path(__file__).parent
DATA = ROOT / "data"

st.set_page_config(page_title="TransitionIQ", page_icon="📊", layout="wide")
st.title("TransitionIQ")
st.caption("Explainable retirement portfolio-transition decision support. Illustrative planning tool — not investment, tax, or legal advice.")

assumptions = load_assumptions(DATA / "assumptions.json")
personas = load_personas(DATA / "personas.csv")
portfolio = load_portfolios(DATA / "demo_portfolios.csv")

with st.sidebar:
    st.header("Analysis controls")
    persona_id = st.selectbox("Client persona", list(personas), format_func=lambda item: personas[item].name)
    years = st.slider("Illustrative comparison horizon", 3, 15, 10)
    st.info("The prototype uses supplied annual return/risk assumptions to create an illustrative path. Replace these with cited total-return series before submission.")

persona = personas[persona_id]
client_portfolio = portfolio.loc[portfolio.persona_id == persona_id]
if client_portfolio.empty:
    st.error("No portfolio was configured for this persona.")
    st.stop()

result = analyze(client_portfolio, persona, assumptions)
recommendation = result["recommendation"]

st.subheader(f"Recommendation: {recommendation['action']}")
st.write(recommendation["rationale"])
col1, col2, col3, col4 = st.columns(4)
col1.metric("Transition cost", f"${result['transition_costs']['total_transition_cost']:,.0f}")
col2.metric("Break-even", "Not reached" if result["break_even_years"] is None else f"{result['break_even_years']:.1f} years")
col3.metric("Current retirement success", f"{result['current_retirement']['success_probability']:.1%}")
col4.metric("Proposed retirement success", f"{result['proposed_retirement']['success_probability']:.1%}")

st.divider()
left, right = st.columns(2)
with left:
    st.subheader("Portfolio economics")
    metric_table = pd.DataFrame([
        {"Metric": "Gross expected return", "Current": result["current"]["gross_return"], "Proposed": result["proposed"]["gross_return"]},
        {"Metric": "Annual fees", "Current": result["current"]["annual_fees"], "Proposed": result["proposed"]["annual_fees"]},
        {"Metric": "Net expected return", "Current": result["current"]["net_return"], "Proposed": result["proposed"]["net_return"]},
        {"Metric": "Volatility", "Current": result["current"]["volatility"], "Proposed": result["proposed"]["volatility"]},
        {"Metric": "Liquidity score", "Current": result["current"]["liquidity_score"], "Proposed": result["proposed"]["liquidity_score"]},
    ])
    st.dataframe(metric_table.style.format({"Current": ".2%", "Proposed": ".2%"}), hide_index=True, width="stretch")
with right:
    st.subheader("Transition-cost waterfall")
    costs = result["transition_costs"]
    cost_frame = pd.DataFrame({"Component": ["Capital-gains tax", "Surrender charges", "Transaction cost"], "Amount": [costs["capital_gains_tax"], costs["surrender_charges"], costs["transaction_cost"]]})
    st.plotly_chart(px.bar(cost_frame, x="Component", y="Amount", text_auto="$.0f", color="Component"), width="stretch")

st.subheader("Illustrative net-value path")
path = pd.concat([
    result["current_path"].assign(strategy="Current"),
    result["proposed_path"].assign(strategy="Proposed"),
])
st.plotly_chart(px.line(path, x="date", y="value", color="strategy", labels={"value": "Portfolio value", "date": "Month"}), width="stretch")

st.subheader("Retirement outcomes through age 90")
retirement = pd.DataFrame([
    {"Strategy": "Current", "Success probability": result["current_retirement"]["success_probability"], "Median terminal wealth": result["current_retirement"]["median_terminal_wealth"], "10th-percentile terminal wealth": result["current_retirement"]["p10_terminal_wealth"]},
    {"Strategy": "Proposed", "Success probability": result["proposed_retirement"]["success_probability"], "Median terminal wealth": result["proposed_retirement"]["median_terminal_wealth"], "10th-percentile terminal wealth": result["proposed_retirement"]["p10_terminal_wealth"]},
])
st.dataframe(retirement.style.format({"Success probability": ".1%", "Median terminal wealth": "${:,.0f}", "10th-percentile terminal wealth": "${:,.0f}"}), hide_index=True, width="stretch")

with st.expander("Methodology, disclosures, and reversal condition"):
    st.write(f"**Recommendation reversal condition:** {recommendation['reversal_condition']}")
    st.write("Tax calculations apply configurable simplified long-term capital-gains rates to taxable unrealized gains. Traditional IRA positions are excluded from this capital-gains calculation. The return path is illustrative, not a historical back-test or forecast.")
    st.json({"tax_year": assumptions["tax_year"], "assumptions": assumptions["notes"]})

export = {key: value for key, value in result.items() if key not in {"current_path", "proposed_path"}}
st.download_button("Download analysis JSON", data=json.dumps(export, indent=2, default=str), file_name=f"transitioniq_{persona_id}.json", mime="application/json")
