# BlackRock Hackathon - Self-Saving for Your Retirement

FastAPI service for automated micro-savings through expense rounding. Applies temporal savings rules (q / p / k periods), validates financial transactions, and projects inflation-adjusted returns across NPS and NIFTY 50 Index Fund.

## Requirements

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Docker | 24+ |

## Project Structure

```
app/
├── main.py
├── core/
│   ├── config.py
│   └── state.py
├── models/
│   ├── transaction.py
│   ├── returns.py
│   └── performance.py
├── services/
│   ├── transaction_service.py
│   └── returns_service.py
└── api/v1/routes/
    ├── transactions.py
    ├── returns.py
    └── performance.py
test/
├── conftest.py
├── test_transactions.py
└── test_returns.py
```

## Running Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 5477 --reload
```

API: `http://localhost:5477` | Docs: `http://localhost:5477/docs`

## Running with Docker

```bash
docker build -t blk-hacking-ind-winson .
docker run -d -p 5477:5477 blk-hacking-ind-winson
```

## Running Tests

```bash
pytest test/ -v
```

## API Endpoints

All endpoints are prefixed with `/blackrock/challenge/v1`.

### `POST /transactions:parse`

Enriches each expense with `ceiling` (next multiple of 100) and `remanent` (ceiling − amount).

**Request:**
```json
[
  { "date": "2023-10-12 20:15:00", "amount": 250 }
]
```

**Response:**
```json
[
  { "date": "2023-10-12 20:15:00", "amount": 250, "ceiling": 300, "remanent": 50 }
]
```

---

### `POST /transactions:validator`

Rejects negative amounts and duplicate timestamps.

**Request:**
```json
{
  "wage": 50000,
  "transactions": [
    { "date": "2023-10-12 20:15:00", "amount": 250, "ceiling": 300, "remanent": 50 }
  ]
}
```

**Response:**
```json
{ "valid": [...], "invalid": [] }
```

---

### `POST /transactions:filter`

Applies q / p / k period rules to transactions.

- **q** - replace remanent with fixed value (latest-start period wins)
- **p** - add extra to remanent (all matching periods summed)
- **k** - flag `inKPeriod: true` if transaction falls within range

**Request:**
```json
{
  "q": [{ "fixed": 0, "start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:59" }],
  "p": [{ "extra": 25, "start": "2023-10-01 08:00:00", "end": "2023-12-31 19:59:59" }],
  "k": [{ "start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:59" }],
  "transactions": [
    { "date": "2023-10-12 20:15:00", "amount": 250, "ceiling": 300, "remanent": 50 }
  ]
}
```

---

### `POST /returns:nps` and `POST /returns:index`

Calculates inflation-adjusted returns. NPS uses 7.11% annually with tax benefit. Index uses 14.49%, no tax benefit.

**Request:**
```json
{
  "age": 29,
  "wage": 50000,
  "inflation": 5.5,
  "q": [{ "fixed": 0, "start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:59" }],
  "p": [{ "extra": 25, "start": "2023-10-01 08:00:00", "end": "2023-12-31 19:59:59" }],
  "k": [{ "start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:59" }],
  "transactions": [
    { "date": "2023-10-12 20:15:00", "amount": 250 },
    { "date": "2023-02-28 15:49:00", "amount": 375 },
    { "date": "2023-07-01 21:59:00", "amount": 620 },
    { "date": "2023-12-17 08:09:00", "amount": 480 }
  ]
}
```

**Response (NPS example):**
```json
{
  "transactionsTotalAmount": 1725.0,
  "transactionsTotalCeiling": 1900.0,
  "savingsByDates": [
    {
      "start": "2023-01-01 00:00:00",
      "end": "2023-12-31 23:59:59",
      "amount": 145.0,
      "profits": 86.88,
      "taxBenefit": 0.0
    }
  ]
}
```

**Formulas:**
```
t             = max(60 - age, 5)
A             = P × (1 + r)^t
A_real        = A / (1 + inflation)^t
profits       = A_real - P
NPS_Deduction = min(invested, 10% of annual_income, 200000)
taxBenefit    = Tax(income) - Tax(income - NPS_Deduction)
```

**Tax slabs:**

| Income | Rate |
|--------|------|
| 0 – 7,00,000 | 0% |
| 7,00,001 – 10,00,000 | 10% on amount above 7L |
| 10,00,001 – 12,00,000 | 15% on amount above 10L |
| 12,00,001 – 15,00,000 | 20% on amount above 12L |
| Above 15,00,000 | 30% on amount above 15L |

---

### `GET /performance`

Returns process uptime, memory usage, and thread count.

```json
{ "time": "00:01:23.456", "memory": "45.23 MB", "threads": 4 }
```
