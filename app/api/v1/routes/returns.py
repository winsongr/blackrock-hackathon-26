from fastapi import APIRouter

from app.models.returns import ReturnsRequest, ReturnsResponse, SavingsByDate
from app.models.transaction import Expense
from app.services.returns_service import calculate_index, calculate_nps
from app.services.transaction_service import (
    filter_by_periods,
    group_by_k_periods,
    parse_transactions,
    validate_transactions,
)

router = APIRouter(tags=["returns"])


def _pipeline(body: ReturnsRequest) -> tuple[list, list, float, float]:
    expenses = [Expense(date=tx.date, amount=tx.amount) for tx in body.transactions]

    parsed = parse_transactions(expenses)
    validated = validate_transactions(body.wage, parsed)
    valid_txs = validated["valid"]

    filtered = filter_by_periods(valid_txs, body.q, body.p, body.k)
    savings_by_dates = group_by_k_periods(filtered["valid"], body.k)

    total_amount = sum(tx.amount for tx in valid_txs)
    total_ceiling = sum(tx.ceiling for tx in valid_txs)

    return savings_by_dates, valid_txs, total_amount, total_ceiling


@router.post("/returns:nps", response_model=ReturnsResponse)
def nps_returns(body: ReturnsRequest) -> ReturnsResponse:
    savings_by_dates, _, total_amount, total_ceiling = _pipeline(body)
    savings = calculate_nps(savings_by_dates, body.age, body.wage, body.inflation)

    return ReturnsResponse(
        transactionsTotalAmount=total_amount,
        transactionsTotalCeiling=total_ceiling,
        savingsByDates=[SavingsByDate(**s) for s in savings],
    )


@router.post("/returns:index", response_model=ReturnsResponse)
def index_returns(body: ReturnsRequest) -> ReturnsResponse:
    savings_by_dates, _, total_amount, total_ceiling = _pipeline(body)
    savings = calculate_index(savings_by_dates, body.age, body.inflation)

    return ReturnsResponse(
        transactionsTotalAmount=total_amount,
        transactionsTotalCeiling=total_ceiling,
        savingsByDates=[SavingsByDate(**s) for s in savings],
    )
