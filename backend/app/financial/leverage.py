"""Deterministic leverage and solvency calculations (Debt/Equity, Debt/EBITDA, Interest Coverage)."""
from typing import List, Optional
from app.financial.schemas import LeverageAnalysis, Metric
from app.schemas.financial import HistoricalFinancial


def calculate_leverage_analysis(
    financials: List[HistoricalFinancial], sector: Optional[str] = None
) -> LeverageAnalysis:
    """
    Computes deterministic leverage and solvency ratios for the latest fiscal period.
    Defensively handles negative equity, missing debt, and undisclosed interest expense.
    """
    if not financials:
        return LeverageAnalysis()

    sorted_fin = sorted(financials, key=lambda x: x.fiscal_year)
    latest = sorted_fin[-1]

    total_debt = latest.total_debt
    equity = latest.stockholders_equity

    # 1. Debt-to-Equity Ratio
    de_val = None
    de_warning = None
    if total_debt is not None and equity is not None:
        if equity > 0:
            de_val = total_debt / equity
        else:
            de_warning = "Shareholders' equity is non-positive; Debt-to-Equity ratio is distorted."
    elif total_debt is None and equity is not None:
        de_warning = "Total debt line item unavailable in SEC filing."
    elif equity is None:
        de_warning = "Shareholders' equity line item unavailable in SEC filing."

    # 2. Debt-to-EBITDA (Strict: only if EBITDA can be reliably derived, otherwise None)
    debt_ebitda_val = None
    debt_ebitda_warning = "EBITDA cannot be reliably derived without separate depreciation & amortization disclosures."

    # 3. Interest Coverage (Operating Income / Interest Expense)
    int_cov_val = None
    int_cov_warning = "Interest expense not separately isolated in standardized 10-K filing."

    # 4. Assemble Explainable Metric Objects
    metrics = {
        "debt_to_equity": Metric(
            value=de_val,
            unit="ratio",
            formula="Total Debt / Shareholders' Equity",
            source_fields=["total_debt", "stockholders_equity"],
            status="available" if de_val is not None else "unavailable",
            warning=de_warning,
        ),
        "debt_to_ebitda": Metric(
            value=debt_ebitda_val,
            unit="multiple",
            formula="Total Debt / EBITDA",
            source_fields=["total_debt", "ebitda"],
            status="unavailable",
            warning=debt_ebitda_warning,
        ),
        "interest_coverage": Metric(
            value=int_cov_val,
            unit="ratio",
            formula="Operating Income / Interest Expense",
            source_fields=["operating_income", "interest_expense"],
            status="unavailable",
            warning=int_cov_warning,
        ),
    }

    return LeverageAnalysis(
        debt_to_equity=de_val,
        debt_to_ebitda=debt_ebitda_val,
        interest_coverage=int_cov_val,
        total_debt=total_debt,
        stockholders_equity=equity,
        metrics=metrics,
    )