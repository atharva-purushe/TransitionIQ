# TransitionIQ

**Explainable retirement portfolio-transition decision support.** The application compares a client’s current portfolio with a proposed strategy after capital-gains taxes, surrender charges, transaction costs, recurring fees, risk, liquidity, and retirement-income sustainability.

> Educational decision support only. Not investment, tax, or legal advice. The included tax and return assumptions are illustrative and must be replaced with cited, current sources before any client or competition use.

## Current MVP

- Validates portfolio input schema and supports taxable and Traditional IRA treatment.
- Calculates realized gains, simplified capital-gains tax, surrender charges, transaction cost, and transition break-even.
- Compares gross/net expected returns, risk, liquidity, and modeled drawdown statistics.
- Simulates retirement from the selected retirement age through age 90 using 5,000 annual return paths.
- Generates an explainable `RETAIN`, `TRANSITION`, or `PARTIAL TRANSITION` recommendation with an explicit reversal condition.
- Provides a Streamlit advisor workflow and downloadable result JSON.

## Run

```powershell
cd D:\TransitionIQ
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest
streamlit run app.py
```

## Input contracts

`data/personas.csv` contains client goals, retirement assumptions, state, and simplified tax rates.

`data/demo_portfolios.csv` requires one or more `current` rows and one or more `proposed` rows for each persona. Required columns:

```text
persona_id, strategy, ticker, asset_class, account_type, market_value, cost_basis,
annual_return, annual_volatility, expense_ratio, advisory_fee, surrender_charge, liquidity_score
```

`account_type` currently recognizes `taxable`, `traditional_ira`, and `roth`. The prototype applies long-term capital-gains tax only to taxable unrealized gains.

## Methodology and limitations

- The app’s graph uses a seeded **illustrative** return-path projection derived from supplied annual return/risk assumptions. It is not a historical back-test.
- Retirement paths are independent lognormal simulations, not forecasts; no guarantee is implied.
- Portfolio volatility is a simple weighted approximation; a production implementation must use return-series covariance.
- Tax rates and account rules are simplified. Source, version, jurisdiction, and calculation method must be recorded in `docs/assumptions_register.md` before submission.
- Future build phases: sourced total-return pipeline, covariance-aware optimization, investor-ready PDF export, source registry, and historical block-bootstrap simulations.

## Verification

`tests/test_engine.py` proves taxable-gain and surrender-charge handling on the supplied representative persona, then exercises the complete recommendation flow.
