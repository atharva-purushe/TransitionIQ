# Assumptions Register

| Area | Current prototype assumption | Required hardening before submission |
|---|---|---|
| Tax law | Configurable simplified long-term federal and state capital-gains rates | Cite current U.S. federal and state primary sources; implement brackets, holding periods, and account-specific rules used in the demo. |
| Taxable holdings | Tax charged on positive `market_value - cost_basis` upon full sale | Support lot-level cost basis and partial sales. |
| Traditional IRA | No capital-gains tax applied at transition | Document treatment separately from future withdrawal taxation. |
| Trading costs | 10 bps of current portfolio value | Replace with product/account-specific disclosed costs. |
| Returns | Supplied annual assumptions generate a seeded illustrative path | Use cited adjusted total-return data and disclose coverage, proxies, and dividend handling. |
| Retirement | Inflation-adjusted annual spending gap through age 90 | Validate spending, other income, inflation, and longevity assumptions per persona. |
| Recommendation | Net return, retirement success, break-even, and liquidity guardrails | Calibrate thresholds and add advisor-review controls. |

Every generated report must display the as-of date, data sources, tax year, account assumptions, limitations, and “not investment advice” disclosure.
