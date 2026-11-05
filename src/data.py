from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .models import Persona

REQUIRED_PORTFOLIO_COLUMNS = {
    "persona_id", "strategy", "ticker", "asset_class", "account_type", "market_value",
    "cost_basis", "annual_return", "annual_volatility", "expense_ratio", "advisory_fee",
    "surrender_charge", "liquidity_score",
}


def load_assumptions(path: str | Path) -> dict:
    with open(path, encoding="utf-8") as source:
        return json.load(source)


def load_personas(path: str | Path) -> dict[str, Persona]:
    frame = pd.read_csv(path)
    return {
        row.persona_id: Persona(**row._asdict())
        for row in frame.itertuples(index=False)
    }


def load_portfolios(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    missing = REQUIRED_PORTFOLIO_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"Portfolio file is missing required columns: {sorted(missing)}")
    if (frame["market_value"] < 0).any() or (frame["cost_basis"] < 0).any():
        raise ValueError("market_value and cost_basis must be non-negative")
    if not frame["strategy"].isin(["current", "proposed"]).all():
        raise ValueError("strategy must be either 'current' or 'proposed'")
    return frame
