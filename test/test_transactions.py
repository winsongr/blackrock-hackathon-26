# Test type: integration
# Validation: /transactions:parse, :validator, :filter
# Command: pytest test/test_transactions.py -v

from fastapi.testclient import TestClient

BASE_URL = "/blackrock/challenge/v1"


class TestParse:
    def test_basic_rounding(self, client: TestClient):
        res = client.post(f"{BASE_URL}/transactions:parse", json=[{"date": "2023-10-12 20:15:00", "amount": 250}])
        assert res.status_code == 200
        data = res.json()
        assert data[0]["ceiling"] == 300
        assert data[0]["remanent"] == 50

    def test_exact_multiple_of_100(self, client: TestClient):
        res = client.post(f"{BASE_URL}/transactions:parse", json=[{"date": "2023-01-01 00:00:00", "amount": 500}])
        assert res.status_code == 200
        data = res.json()
        assert data[0]["ceiling"] == 500
        assert data[0]["remanent"] == 0

    def test_spec_example(self, client: TestClient):
        expenses = [
            {"date": "2023-10-12 20:15:00", "amount": 250},
            {"date": "2023-02-28 15:49:00", "amount": 375},
            {"date": "2023-07-01 21:59:00", "amount": 620},
            {"date": "2023-12-17 08:09:00", "amount": 480},
        ]
        res = client.post(f"{BASE_URL}/transactions:parse", json=expenses)
        assert res.status_code == 200
        data = res.json()

        expected = [(300, 50), (400, 25), (700, 80), (500, 20)]
        for tx, (ceiling, remanent) in zip(data, expected):
            assert tx["ceiling"] == ceiling
            assert tx["remanent"] == remanent

    def test_empty_list(self, client: TestClient):
        res = client.post(f"{BASE_URL}/transactions:parse", json=[])
        assert res.status_code == 200
        assert res.json() == []


class TestValidator:
    def _tx(self, date: str, amount: float):
        ceiling = (int(amount // 100) + (1 if amount % 100 != 0 else 0)) * 100
        return {"date": date, "amount": amount, "ceiling": float(ceiling), "remanent": ceiling - amount}

    def test_valid_transactions(self, client: TestClient):
        body = {
            "wage": 50000,
            "transactions": [
                self._tx("2023-01-01 00:00:00", 250),
                self._tx("2023-02-01 00:00:00", 375),
            ],
        }
        res = client.post(f"{BASE_URL}/transactions:validator", json=body)
        assert res.status_code == 200
        data = res.json()
        assert len(data["valid"]) == 2
        assert len(data["invalid"]) == 0

    def test_duplicate_date_rejected(self, client: TestClient):
        tx = self._tx("2023-01-01 00:00:00", 250)
        body = {"wage": 50000, "transactions": [tx, tx]}
        res = client.post(f"{BASE_URL}/transactions:validator", json=body)
        assert res.status_code == 200
        data = res.json()
        assert len(data["valid"]) == 1
        assert len(data["invalid"]) == 1
        assert "Duplicate" in data["invalid"][0]["message"]

    def test_negative_amount_rejected(self, client: TestClient):
        body = {
            "wage": 50000,
            "transactions": [
                {"date": "2023-01-01 00:00:00", "amount": -100, "ceiling": 0, "remanent": 0}
            ],
        }
        res = client.post(f"{BASE_URL}/transactions:validator", json=body)
        assert res.status_code == 200
        data = res.json()
        assert len(data["valid"]) == 0
        assert len(data["invalid"]) == 1
        assert "Negative" in data["invalid"][0]["message"]


class TestFilter:
    BASE_TRANSACTIONS = [
        {"date": "2023-10-12 20:15:00", "amount": 250, "ceiling": 300, "remanent": 50},
        {"date": "2023-02-28 15:49:00", "amount": 375, "ceiling": 400, "remanent": 25},
        {"date": "2023-07-01 21:59:00", "amount": 620, "ceiling": 700, "remanent": 80},
        {"date": "2023-12-17 08:09:00", "amount": 480, "ceiling": 500, "remanent": 20},
    ]

    def test_q_period_zeros_out_remanent(self, client: TestClient):
        body = {
            "q": [{"fixed": 0, "start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:59"}],
            "p": [],
            "k": [],
            "transactions": self.BASE_TRANSACTIONS,
        }
        res = client.post(f"{BASE_URL}/transactions:filter", json=body)
        assert res.status_code == 200
        valid = res.json()["valid"]
        jul = next(t for t in valid if "07-01" in t["date"])
        assert jul["remanent"] == 0

    def test_p_period_adds_extra(self, client: TestClient):
        body = {
            "q": [],
            "p": [{"extra": 25, "start": "2023-10-01 08:00:00", "end": "2023-12-31 19:59:59"}],
            "k": [],
            "transactions": self.BASE_TRANSACTIONS,
        }
        res = client.post(f"{BASE_URL}/transactions:filter", json=body)
        assert res.status_code == 200
        valid = res.json()["valid"]

        by_date = {t["date"]: t["remanent"] for t in valid}
        assert by_date["2023-10-12 20:15:00"] == 75   # 50 + 25
        assert by_date["2023-02-28 15:49:00"] == 25   # no match
        assert by_date["2023-07-01 21:59:00"] == 80   # outside p range
        assert by_date["2023-12-17 08:09:00"] == 45   # 20 + 25

    def test_q_and_p_combined(self, client: TestClient):
        body = {
            "q": [{"fixed": 0, "start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:59"}],
            "p": [{"extra": 25, "start": "2023-10-01 08:00:00", "end": "2023-12-31 19:59:59"}],
            "k": [{"start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:59"}],
            "transactions": self.BASE_TRANSACTIONS,
        }
        res = client.post(f"{BASE_URL}/transactions:filter", json=body)
        assert res.status_code == 200
        valid = res.json()["valid"]

        by_date = {t["date"]: t["remanent"] for t in valid}
        assert by_date["2023-10-12 20:15:00"] == 75
        assert by_date["2023-02-28 15:49:00"] == 25
        assert by_date["2023-07-01 21:59:00"] == 0
        assert by_date["2023-12-17 08:09:00"] == 45

    def test_k_period_flag(self, client: TestClient):
        body = {
            "q": [],
            "p": [],
            "k": [{"start": "2023-03-01 00:00:00", "end": "2023-11-30 23:59:59"}],
            "transactions": self.BASE_TRANSACTIONS,
        }
        res = client.post(f"{BASE_URL}/transactions:filter", json=body)
        assert res.status_code == 200
        valid = res.json()["valid"]

        by_date = {t["date"]: t["inKPeriod"] for t in valid}
        assert by_date["2023-10-12 20:15:00"] is True   # within Mar–Nov
        assert by_date["2023-07-01 21:59:00"] is True   # within Mar–Nov
        assert by_date["2023-02-28 15:49:00"] is False  # before March
        assert by_date["2023-12-17 08:09:00"] is False  # after November
