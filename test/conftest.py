# Test type: fixture
# Validation: shared TestClient for all test modules
# Command: pytest test/ -v

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)
