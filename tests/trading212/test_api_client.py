import base64
from unittest.mock import MagicMock, patch

import pytest

from src.trading212.api_client import Trading212APIClient


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("TRADING212_API_KEY", "test_key")
    monkeypatch.setenv("TRADING212_API_SECRET", "test_secret")


def test_init_with_env_variables(mock_env):
    client = Trading212APIClient()
    assert client.headers["Authorization"].startswith("Basic ")
    expected_credentials = b"test_key:test_secret"
    encoded_credentials = base64.b64encode(expected_credentials).decode("utf-8")
    assert client.headers["Authorization"] == f"Basic {encoded_credentials}"


def test_init_missing_env_variables():
    with pytest.raises(ValueError, match="environment variables must be set"):
        Trading212APIClient()


@patch("requests.get")
def test_fetch_paginated_success(mock_get, mock_env):
    mock_response1 = MagicMock()
    mock_response1.status_code = 200
    mock_response1.json.return_value = {
        "items": [{"id": 1}, {"id": 2}],
        "nextPagePath": "/api/v0/equity/history/orders?cursor=2",
    }
    mock_response2 = MagicMock()
    mock_response2.status_code = 200
    mock_response2.json.return_value = {"items": [{"id": 3}], "nextPagePath": None}
    mock_get.side_effect = [mock_response1, mock_response2]

    client = Trading212APIClient()
    with patch("time.sleep"):  # Mock sleep to speed up test
        items = client._fetch_paginated("/api/v0/equity/history/orders")

    assert len(items) == 3
    assert items == [{"id": 1}, {"id": 2}, {"id": 3}]
    assert mock_get.call_count == 2


@patch("requests.get")
def test_fetch_paginated_api_error(mock_get, mock_env):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_get.return_value = mock_response

    client = Trading212APIClient()
    with patch("time.sleep"):
        items = client._fetch_paginated("/api/v0/equity/history/orders")

    assert len(items) == 0
    assert mock_get.call_count == 1
