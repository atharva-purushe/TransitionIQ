from pathlib import Path

from src.data import load_assumptions, load_personas, load_portfolios
from src.engine import analyze, transition_costs

ROOT = Path(__file__).parents[1]


def test_transition_costs_tax_only_taxable_gain():
    portfolio = load_portfolios(ROOT / "data" / "demo_portfolios.csv")
    persona = load_personas(ROOT / "data" / "personas.csv")["pre_retirement_58"]
    current = portfolio.query("persona_id == 'pre_retirement_58' and strategy == 'current'")
    costs = transition_costs(current, persona)
    assert costs["realized_capital_gains"] == 105000
    assert costs["capital_gains_tax"] == 15750
    assert costs["surrender_charges"] == 9600


def test_end_to_end_analysis_rejects_transition_when_retirement_success_is_inadequate():
    portfolio = load_portfolios(ROOT / "data" / "demo_portfolios.csv")
    persona = load_personas(ROOT / "data" / "personas.csv")["pre_retirement_58"]
    output = analyze(portfolio.query("persona_id == 'pre_retirement_58'"), persona, load_assumptions(ROOT / "data" / "assumptions.json"))
    assert output["recommendation"]["action"] == "RETAIN"
    assert output["transition_costs"]["total_transition_cost"] > 0
    assert output["proposed_retirement"]["success_probability"] < 0.70
    assert len(output["current_path"]) == 120
