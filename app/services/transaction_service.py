from __future__ import annotations

import math
from datetime import datetime
from typing import Any

from app.models.transaction import (
    Expense,
    InvalidTransaction,
    KPeriod,
    PPeriod,
    QPeriod,
    Transaction,
    TransactionFiltered,
)

_FMT = "%Y-%m-%d %H:%M:%S"


def _dt(s: str) -> datetime:
    return datetime.strptime(s, _FMT)  # noqa: DTZ007


def parse_transactions(expenses: list[Expense]) -> list[Transaction]:
    result: list[Transaction] = []
    for exp in expenses:
        amount = exp.amount
        ceiling = math.ceil(amount / 100) * 100 if amount % 100 != 0 else amount
        remanent = ceiling - amount
        result.append(
            Transaction(date=exp.date, amount=amount, ceiling=ceiling, remanent=remanent)
        )
    return result


def validate_transactions(
    wage: float,
    transactions: list[Transaction],
) -> dict[str, list[Any]]:
    valid: list[Transaction] = []
    invalid: list[InvalidTransaction] = []
    seen_dates: set[str] = set()

    for tx in transactions:
        if tx.amount < 0:
            invalid.append(
                InvalidTransaction(**tx.model_dump(), message="Negative amounts are not allowed")
            )
            continue

        if tx.date in seen_dates:
            invalid.append(
                InvalidTransaction(**tx.model_dump(), message="Duplicate transaction")
            )
            continue

        seen_dates.add(tx.date)
        valid.append(tx)

    return {"valid": valid, "invalid": invalid}


def filter_by_periods(
    transactions: list[Transaction],
    q_periods: list[QPeriod],
    p_periods: list[PPeriod],
    k_periods: list[KPeriod],
) -> dict[str, list[Any]]:
    valid: list[TransactionFiltered] = []
    invalid: list[InvalidTransaction] = []
    seen_dates: set[str] = set()

    for tx in transactions:
        if tx.amount < 0:
            invalid.append(
                InvalidTransaction(**tx.model_dump(), message="Negative amounts are not allowed")
            )
            continue

        if tx.date in seen_dates:
            invalid.append(
                InvalidTransaction(**tx.model_dump(), message="Duplicate transaction")
            )
            continue

        seen_dates.add(tx.date)
        tx_dt = _dt(tx.date)

        # q: latest-start wins; stable sort keeps list order on ties
        remanent = tx.remanent
        matching_q = [q for q in q_periods if _dt(q.start) <= tx_dt <= _dt(q.end)]
        if matching_q:
            matching_q.sort(key=lambda q: q.start, reverse=True)
            remanent = matching_q[0].fixed

        # p: add all matching extras
        for p in p_periods:
            if _dt(p.start) <= tx_dt <= _dt(p.end):
                remanent += p.extra

        in_k = any(_dt(k.start) <= tx_dt <= _dt(k.end) for k in k_periods)

        valid.append(
            TransactionFiltered(
                date=tx.date,
                amount=tx.amount,
                ceiling=tx.ceiling,
                remanent=remanent,
                inKPeriod=in_k,
            )
        )

    return {"valid": valid, "invalid": invalid}


def group_by_k_periods(
    transactions: list[TransactionFiltered],
    k_periods: list[KPeriod],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for k in k_periods:
        k_start, k_end = _dt(k.start), _dt(k.end)
        total = sum(tx.remanent for tx in transactions if k_start <= _dt(tx.date) <= k_end)
        result.append({"start": k.start, "end": k.end, "amount": total})
    return result
