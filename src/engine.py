from __future__ import annotations

import math
from dataclasses import asdict

import numpy as np
import pandas as pd

from .models import Persona, Recommendation


def _strategy_rows(portfolio: pd.DataFrame, strategy: str) -> pd.DataFrame:
    rows = portfolio.loc[portfolio["strategy"] == strategy].copy()
    if rows.empty:
        raise ValueError(f"No {strategy!r} holdings supplied")
    return rows


def weighted_strategy_metrics(portfolio: pd.DataFrame, strategy: str) -> dict:
    rows = _strategy_rows(portfolio, strategy)
    total = float(rows.market_value.sum())
    weights = rows.market_value / total
    gross_return = float((weights * rows.annual_return).sum())
    annual_fees = float((weights * (rows.expense_ratio + rows.advisory_fee)).sum())
    volatility = float(np.sqrt(np.sum((weights * rows.annual_volatility) ** 2)))
    liquidity = float((weights * rows.liquidity_score).sum())
    return {
        "strategy": strategy,
        "market_value": total,
        "gross_return": gross_return,
        "annual_fees": annual_fees,
        "net_return": gross_return - annual_fees,
        "volatility": volatility,
        "liquidity_score": liquidity,
    }


def transition_costs(current: pd.DataFrame, persona: Persona) -> dict:
    taxable = current.loc[current.account_type == "taxable"].copy()
    gains = (taxable.market_value - taxable.cost_basis).clip(lower=0)
    tax_rate = persona.federal_capital_gains_rate + persona.state_capital_gains_rate
    capital_gains_tax = float((gains * tax_rate).sum())
    surrender_charges = float((current.market_value * current.surrender_charge).sum())
    # A transparent planning assumption: 10 bps to transact all transferred assets.
    transaction_cost = float(current.market_value.sum() * 0.001)
    total = capital_gains_tax + surrender_charges + transaction_cost
    return {
        "realized_capital_gains": float(gains.sum()),
        "capital_gains_tax": capital_gains_tax,
        "surrender_charges": surrender_charges,
        "transaction_cost": transaction_cost,
        "total_transition_cost": total,
    }


def breakeven_years(current_metrics: dict, proposed_metrics: dict, costs: dict) -> float | None:
    annual_net_gain = (proposed_metrics["net_return"] - current_metrics["net_return"]) * current_metrics["market_value"]
    if annual_net_gain <= 0:
        return None
    return costs["total_transition_cost"] / annual_net_gain


def historical_projection(metrics: dict, years: int = 10, seed: int = 17) -> pd.DataFrame:
    """Illustrative return-path projection for a prototype; replace with sourced total-return data for production back-tests."""
    rng = np.random.default_rng(seed)
    monthly_mu = (1 + metrics["net_return"]) ** (1 / 12) - 1
    monthly_sigma = metrics["volatility"] / math.sqrt(12)
    returns = rng.normal(monthly_mu, monthly_sigma, years * 12)
    values = metrics["market_value"] * np.cumprod(1 + returns)
    dates = pd.date_range("2016-01-31", periods=years * 12, freq="ME")
    return pd.DataFrame({"date": dates, "return": returns, "value": values})


def path_metrics(path: pd.DataFrame) -> dict:
    returns = path["return"]
    periods = len(returns)
    cumulative = float(path.value.iloc[-1] / path.value.iloc[0] - 1)
    annualized = (1 + cumulative) ** (12 / periods) - 1
    running_max = path.value.cummax()
    max_drawdown = float((path.value / running_max - 1).min())
    downside = returns[returns < 0]
    downside_deviation = float(downside.std(ddof=0) * math.sqrt(12)) if not downside.empty else 0.0
    sortino = annualized / downside_deviation if downside_deviation else None
    return {"cumulative_return": cumulative, "annualized_return": annualized, "max_drawdown": max_drawdown, "sortino": sortino}


def retirement_simulation(metrics: dict, persona: Persona, assumptions: dict, initial_value: float, seed: int = 41) -> dict:
    years = persona.retirement_years
    simulations = int(assumptions["simulation_count"])
    rng = np.random.default_rng(seed)
    log_mu = math.log1p(metrics["net_return"]) - 0.5 * metrics["volatility"] ** 2
    annual_returns = np.exp(rng.normal(log_mu, metrics["volatility"], (simulations, years))) - 1
    values = np.full(simulations, initial_value, dtype=float)
    depleted = np.zeros(simulations, dtype=bool)
    inflation = float(assumptions["annual_inflation_rate"])
    base_shortfall = max(0.0, persona.annual_retirement_spend - persona.annual_other_income)
    for year in range(years):
        withdrawal = base_shortfall * (1 + inflation) ** year
        values = np.maximum(0.0, values - withdrawal) * (1 + annual_returns[:, year])
        depleted |= values <= 0
    return {
        "success_probability": float((~depleted).mean()),
        "median_terminal_wealth": float(np.median(values)),
        "p10_terminal_wealth": float(np.quantile(values, 0.10)),
        "median_annual_income_gap": base_shortfall,
    }


def recommend(current: dict, proposed: dict, costs: dict, current_retirement: dict, proposed_retirement: dict, break_even: float | None) -> Recommendation:
    success_delta = proposed_retirement["success_probability"] - current_retirement["success_probability"]
    liquidity_drop = current["liquidity_score"] - proposed["liquidity_score"]
    if proposed_retirement["success_probability"] < 0.70:
        return Recommendation("RETAIN", "Neither strategy has an adequate modeled probability of funding retirement through age 90; do not incur transition costs until the retirement plan is redesigned.", "Reassess after changing spending needs, retirement timing, savings, guaranteed income, or a fully constrained alternative allocation.", "High")
    if proposed["net_return"] <= current["net_return"] or success_delta < -0.01:
        return Recommendation("RETAIN", "The proposed strategy does not improve net return or retirement-success probability after recurring fees and transition costs.", "Reassess if proposed net return rises or transition costs materially fall.", "High")
    if break_even is None or break_even > 7 or liquidity_drop > 0.25:
        return Recommendation("PARTIAL TRANSITION", "The proposed strategy has long-run merit, but its upfront cost or liquidity trade-off is too high for a full immediate move.", "A full transition becomes viable if the break-even period falls below seven years and liquidity remains within the client reserve target.", "Moderate")
    return Recommendation("TRANSITION", "The proposed strategy improves net expected return and retirement success with a reasonable recovery period for upfront costs.", "Retain instead if sequence-of-returns risk or transition costs exceed the disclosed sensitivity threshold.", "Moderate")


def analyze(portfolio: pd.DataFrame, persona: Persona, assumptions: dict) -> dict:
    current_rows = _strategy_rows(portfolio, "current")
    current = weighted_strategy_metrics(portfolio, "current")
    proposed = weighted_strategy_metrics(portfolio, "proposed")
    costs = transition_costs(current_rows, persona)
    break_even = breakeven_years(current, proposed, costs)
    current_path = historical_projection(current)
    proposed_path = historical_projection(proposed)
    current_retirement = retirement_simulation(current, persona, assumptions, current["market_value"])
    proposed_retirement = retirement_simulation(proposed, persona, assumptions, max(0.0, proposed["market_value"] - costs["total_transition_cost"]))
    decision = recommend(current, proposed, costs, current_retirement, proposed_retirement, break_even)
    return {
        "persona": asdict(persona), "current": current, "proposed": proposed, "transition_costs": costs,
        "break_even_years": break_even, "current_path": current_path, "proposed_path": proposed_path,
        "current_path_metrics": path_metrics(current_path), "proposed_path_metrics": path_metrics(proposed_path),
        "current_retirement": current_retirement, "proposed_retirement": proposed_retirement,
        "recommendation": asdict(decision),
    }
