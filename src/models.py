from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

AccountType = Literal["taxable", "traditional_ira", "roth"]


@dataclass(frozen=True)
class Persona:
    persona_id: str
    name: str
    current_age: int
    retirement_age: int
    state: str
    federal_capital_gains_rate: float
    state_capital_gains_rate: float
    risk_tolerance: str
    annual_retirement_spend: float
    annual_other_income: float
    liquid_reserve: float
    life_expectancy: int

    @property
    def retirement_years(self) -> int:
        return self.life_expectancy - self.retirement_age


@dataclass(frozen=True)
class Recommendation:
    action: Literal["RETAIN", "TRANSITION", "PARTIAL TRANSITION", "OPTIMIZE ALTERNATIVE"]
    rationale: str
    reversal_condition: str
    confidence: str
