from __future__ import annotations

from pydantic import BaseModel

from app.models.transaction import Expense, KPeriod, PPeriod, QPeriod


class ReturnsRequest(BaseModel):
    age: int
    wage: float
    inflation: float
    q: list[QPeriod] = []
    p: list[PPeriod] = []
    k: list[KPeriod] = []
    transactions: list[Expense]


class SavingsByDate(BaseModel):
    start: str
    end: str
    amount: float
    profits: float
    taxBenefit: float


class ReturnsResponse(BaseModel):
    transactionsTotalAmount: float
    transactionsTotalCeiling: float
    savingsByDates: list[SavingsByDate]
