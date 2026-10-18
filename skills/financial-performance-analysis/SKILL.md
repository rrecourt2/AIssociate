---
name: financial-performance-analysis
description: Use for financial trends, revenue or margin changes, earnings adjustments, profit versus cash, working capital and checked financial tables. For debt service, liquidity and covenants, use repayment-and-structure.
---

# Financial Performance Analysis

Explain material movements, their supported drivers, unexplained effects and the financing implications.

Apply [operating rules](../../shared/operating-rules.md) and the [evidence workflow](../../shared/workflow-contract.md). Use the approved spread and the relevant statements, notes, interim accounts and operating evidence. Use the institution's own methods for sector-specific or regulated-capital cases.

Tools: [register.py](../../tools/register.py), [fin_table.py](../../tools/fin_table.py).

## Analyse

Consult the relevant sections of [financial-analysis-methods.md](../../shared/financial-analysis-methods.md) for comparisons, bridges, adjustments and cash conversion.

Match entity, perimeter, periods, currency, scale and definitions; distinguish actual, forecast and adjusted figures. When fin_table.py transfers spread figures, the mapping must name the entity, perimeter and unit from located cells or a reviewed basis. Never set `trust_formula_values` to get past a refusal.

Use deterministic calculations and keep the formulas, located inputs and rounding in reusable code or an editable workbook. Label calculations you cannot verify as provisional and limit reliance on them.

Select the movements that matter to the case:

- **Revenue and margins:** operating drivers, perimeter and FX changes, accounting effects and earnings quality. Sales growth alone does not establish profitability or collection.
- **Cash conversion:** the profit-to-cash reconciliation and working-capital quality, including seasonality and temporary releases.
- **Investment and funding:** capex, distributions, acquisitions, financing flows and cash restrictions. Separate maintenance from growth capex only where supported.

Test management explanations against notes, operating data and later evidence, keeping the attribution unless they are corroborated. A reconciled bridge still needs a plausible mechanism.

## Deliver

Return located conclusions about earning power, cash conversion and their implications for the current question, with checked calculations, contrary or unexplained evidence, and the basis for any recurring, temporary or recovery assessment. Record them in the register; keep detailed calculations internal. Historical EBITDA alone does not establish debt-service capacity; use repayment-and-structure for material liquidity, maturity or repayment questions.
