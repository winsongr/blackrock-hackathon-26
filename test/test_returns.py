# Test type: integration + unit
# Validation: /returns:nps, /returns:index, calculate_tax
# Command: pytest test/test_returns.py -v

import pytest
from fastapi.testclient import TestClient

from app.services.returns_service import calculate_tax

BASE_URL = "/blackrock/challenge/v1"

SPEC_PAYLOAD = {
    "age": 29,
    "wage": 50000,
    "inflation": 5.5,
    "q": [{"fixed": 0, "start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:59"}],
    "p": [{"extra": 25, "start": "2023-10-01 08:00:00", "end": "2023-12-31 19:59:59"}],
    "k": [
        {"start": "2023-03-01 00:00:00", "end": "2023-11-30 23:59:59"},
        {"start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:59"},
    ],
    "transactions": [
        {"date": "2023-10-12 20:15:00", "amount": 250},
        {"date": "2023-02-28 15:49:00", "amount": 375},
        {"date": "2023-07-01 21:59:00", "amount": 620},
        {"date": "2023-12-17 08:09:00", "amount": 480},
    ],
}


class TestCalculateTax:
    def test_zero_slab(self):
        assert calculate_tax(600_000) == 0.0

    def test_ten_percent_slab(self):
        # 8L → 10% on 1L above 7L = 10,000
        assert calculate_tax(800_000) == pytest.approx(10_000)

    def test_fifteen_percent_slab(self):
        # 11L → 30,000 + 15% on 1L above 10L = 45,000
        assert calculate_tax(1_100_000) == pytest.approx(45_000)

    def test_twenty_percent_slab(self):
        # 13L → 60,000 + 20% on 1L above 12L = 80,000
        assert calculate_tax(1_300_000) == pytest.approx(80_000)

    def test_thirty_percent_slab(self):
        # 16L → 120,000 + 30% on 1L above 15L = 150,000
        assert calculate_tax(1_600_000) == pytest.approx(150_000)


class TestNPSReturns:
    def test_structure(self, client: TestClient):
        res = client.post(f"{BASE_URL}/returns:nps", json=SPEC_PAYLOAD)
        assert res.status_code == 200
        data = res.json()
        assert "transactionsTotalAmount" in data
        assert "transactionsTotalCeiling" in data
        assert len(data["savingsByDates"]) == 2

    def test_k_period_amounts(self, client: TestClient):
        # Mar–Nov → 75; full year → 145 (spec example)
        res = client.post(f"{BASE_URL}/returns:nps", json=SPEC_PAYLOAD)
        savings = res.json()["savingsByDates"]
        assert savings[0]["amount"] == pytest.approx(75)
        assert savings[1]["amount"] == pytest.approx(145)

    def test_zero_tax_benefit_for_low_income(self, client: TestClient):
        # annual income 6L is in 0% slab
        res = client.post(f"{BASE_URL}/returns:nps", json=SPEC_PAYLOAD)
        for s in res.json()["savingsByDates"]:
            assert s["taxBenefit"] == pytest.approx(0.0)

    def test_profit_positive(self, client: TestClient):
        res = client.post(f"{BASE_URL}/returns:nps", json=SPEC_PAYLOAD)
        for s in res.json()["savingsByDates"]:
            assert s["profits"] > 0

    def test_spec_profit_approx(self, client: TestClient):
        # full-year k period → profit ≈ 86.88 (spec example)
        res = client.post(f"{BASE_URL}/returns:nps", json=SPEC_PAYLOAD)
        savings = res.json()["savingsByDates"]
        full_year = next(s for s in savings if "01-01" in s["start"])
        assert full_year["profits"] == pytest.approx(86.88, abs=0.5)


class TestIndexReturns:
    def test_structure(self, client: TestClient):
        res = client.post(f"{BASE_URL}/returns:index", json=SPEC_PAYLOAD)
        assert res.status_code == 200
        assert len(res.json()["savingsByDates"]) == 2

    def test_tax_benefit_always_zero(self, client: TestClient):
        res = client.post(f"{BASE_URL}/returns:index", json=SPEC_PAYLOAD)
        for s in res.json()["savingsByDates"]:
            assert s["taxBenefit"] == 0.0

    def test_higher_profit_than_nps(self, client: TestClient):
        nps = client.post(f"{BASE_URL}/returns:nps", json=SPEC_PAYLOAD).json()
        idx = client.post(f"{BASE_URL}/returns:index", json=SPEC_PAYLOAD).json()
        assert sum(s["profits"] for s in idx["savingsByDates"]) > sum(s["profits"] for s in nps["savingsByDates"])

    def test_spec_profit_approx(self, client: TestClient):
        # full-year k period → profit ≈ 1684.5 (spec example, NIFTY 50)
        res = client.post(f"{BASE_URL}/returns:index", json=SPEC_PAYLOAD)
        savings = res.json()["savingsByDates"]
        full_year = next(s for s in savings if "01-01" in s["start"])
        assert full_year["profits"] == pytest.approx(1684.5, abs=1.0)


class TestPerformance:
    def test_fields_present(self, client: TestClient):
        res = client.get(f"{BASE_URL}/performance")
        assert res.status_code == 200
        data = res.json()
        assert "time" in data
        assert "memory" in data
        assert "threads" in data

    def test_memory_format(self, client: TestClient):
        res = client.get(f"{BASE_URL}/performance")
        memory = res.json()["memory"]
        assert memory.endswith(" MB")
        float(memory.replace(" MB", ""))

    def test_time_format(self, client: TestClient):
        res = client.get(f"{BASE_URL}/performance")
        t = res.json()["time"]
        parts = t.split(":")
        assert len(parts) == 3
        assert "." in parts[2]
