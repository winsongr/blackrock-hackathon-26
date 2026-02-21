from fastapi import APIRouter

from app.models.transaction import (
    Expense,
    FilterRequest,
    FilterResponse,
    Transaction,
    ValidatorRequest,
    ValidatorResponse,
)
from app.services.transaction_service import (
    filter_by_periods,
    parse_transactions,
    validate_transactions,
)

router = APIRouter(tags=["transactions"])


@router.post("/transactions:parse", response_model=list[Transaction])
def parse(expenses: list[Expense]) -> list[Transaction]:
    return parse_transactions(expenses)


@router.post("/transactions:validator", response_model=ValidatorResponse)
def validator(body: ValidatorRequest) -> ValidatorResponse:
    result = validate_transactions(body.wage, body.transactions)
    return ValidatorResponse(**result)


@router.post("/transactions:filter", response_model=FilterResponse)
def filter_transactions(body: FilterRequest) -> FilterResponse:
    result = filter_by_periods(body.transactions, body.q, body.p, body.k)
    return FilterResponse(**result)
