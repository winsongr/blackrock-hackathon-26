from __future__ import annotations

NPS_RATE = 0.0711
INDEX_RATE = 0.1449


def calculate_tax(income: float) -> float:
    # Simplified Indian tax slabs (no standard deduction)
    # 0–7L: 0%, 7L–10L: 10%, 10L–12L: 15%, 12L–15L: 20%, >15L: 30%
    if income <= 700_000:
        return 0.0
    if income <= 1_000_000:
        return (income - 700_000) * 0.10
    if income <= 1_200_000:
        return 30_000 + (income - 1_000_000) * 0.15
    if income <= 1_500_000:
        return 60_000 + (income - 1_200_000) * 0.20
    return 120_000 + (income - 1_500_000) * 0.30


def calculate_nps(
    savings_by_dates: list[dict],
    age: int,
    wage: float,
    inflation: float,
) -> list[dict]:
    annual_income = wage * 12
    t = max(60 - age, 5)
    infl = inflation / 100

    results: list[dict] = []
    for s in savings_by_dates:
        amount: float = s["amount"]

        A = amount * (1 + NPS_RATE) ** t
        real = A / (1 + infl) ** t
        profit = real - amount

        nps_deduction = min(amount, annual_income * 0.10, 200_000)
        tax_benefit = calculate_tax(annual_income) - calculate_tax(annual_income - nps_deduction)

        results.append({
            "start": s["start"],
            "end": s["end"],
            "amount": round(amount, 2),
            "profits": round(profit, 2),
            "taxBenefit": round(tax_benefit, 2),
        })
    return results


def calculate_index(
    savings_by_dates: list[dict],
    age: int,
    inflation: float,
) -> list[dict]:
    t = max(60 - age, 5)
    infl = inflation / 100

    results: list[dict] = []
    for s in savings_by_dates:
        amount: float = s["amount"]

        A = amount * (1 + INDEX_RATE) ** t
        real = A / (1 + infl) ** t
        profit = real - amount

        results.append({
            "start": s["start"],
            "end": s["end"],
            "amount": round(amount, 2),
            "profits": round(profit, 2),
            "taxBenefit": 0.0,
        })
    return results
