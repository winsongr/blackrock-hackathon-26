from __future__ import annotations

from pydantic import BaseModel, field_validator


class Expense(BaseModel):
    date: str
    amount: float

    @field_validator("amount")
    @classmethod
    def amount_must_be_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("amount must be non-negative")
        return v


class Transaction(BaseModel):
    date: str
    amount: float
    ceiling: float
    remanent: float


class TransactionFiltered(Transaction):
    inKPeriod: bool


class InvalidTransaction(Transaction):
    message: str


# ── Period models ──────────────────────────────────────────────────────────────

class QPeriod(BaseModel):
    """Fixed-amount override period."""
    fixed: float
    start: str
    end: str


class PPeriod(BaseModel):
    """Extra-amount addition period."""
    extra: float
    start: str
    end: str


class KPeriod(BaseModel):
    """Evaluation / grouping period."""
    start: str
    end: str


# ── Request / response models ──────────────────────────────────────────────────

class ValidatorRequest(BaseModel):
    wage: float
    transactions: list[Transaction]


class ValidatorResponse(BaseModel):
    valid: list[Transaction]
    invalid: list[InvalidTransaction]


class FilterRequest(BaseModel):
    q: list[QPeriod] = []
    p: list[PPeriod] = []
    k: list[KPeriod] = []
    wage: float = 0.0
    transactions: list[Transaction]


class FilterResponse(BaseModel):
    valid: list[TransactionFiltered]
    invalid: list[InvalidTransaction]
