from datetime import datetime
from unittest.mock import patch

from src.models.transaction import Transaction, TransactionType
from src.trading212.transaction_factory import TransactionFactory


def test_parse_date_valid():
    date_str = "2023-10-27T10:00:00Z"
    parsed_date = TransactionFactory._parse_date(date_str)
    assert parsed_date == datetime(2023, 10, 27, 10, 0, 0)


def test_parse_date_invalid():
    with patch("src.trading212.transaction_factory.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2023, 1, 1)
        mock_datetime.fromisoformat.side_effect = ValueError("Invalid ISO format")
        parsed_date = TransactionFactory._parse_date("invalid-date")
        assert parsed_date == datetime(2023, 1, 1)


def test_from_order_filled():
    order = {
        "id": 1,
        "ticker": "AAPL",
        "direction": "BUY",
        "quantity": 10,
        "price": 150.0,
        "date": "2023-10-27T10:00:00Z",
        "status": "FILLED",
    }
    transaction = TransactionFactory.from_order(order)
    assert isinstance(transaction, Transaction)
    assert transaction.transaction_type == TransactionType.BUY
    assert transaction.signed_amount == -1500.0


def test_from_order_not_filled():
    order = {"status": "PENDING"}
    transaction = TransactionFactory.from_order(order)
    assert transaction is None


def test_from_dividend():
    dividend = {
        "id": 1,
        "ticker": "MSFT",
        "amount": 50.0,
        "date": "2023-10-27T10:00:00Z",
    }
    transaction = TransactionFactory.from_dividend(dividend)
    assert isinstance(transaction, Transaction)
    assert transaction.transaction_type == TransactionType.DIVIDEND
    assert transaction.amount == 50.0


def test_from_transaction_deposit():
    cash_transaction = {
        "id": 1,
        "type": "DEPOSIT",
        "amount": 1000.0,
        "date": "2023-10-27T10:00:00Z",
    }
    transaction = TransactionFactory.from_transaction(cash_transaction)
    assert isinstance(transaction, Transaction)
    assert transaction.transaction_type == TransactionType.DEPOSIT
    assert transaction.amount == 1000.0


def test_create_all_transactions():
    orders = [
        {
            "status": "FILLED",
            "type": "BUY",
            "ticker": "GOOG",
            "quantity": 1,
            "price": 130,
            "date": "2023-01-01T12:00:00Z",
        }
    ]
    dividends = [{"ticker": "AAPL", "amount": 20, "date": "2023-01-02T12:00:00Z"}]
    transactions = [{"type": "DEPOSIT", "amount": 500, "date": "2023-01-03T12:00:00Z"}]

    all_trans = TransactionFactory.create_all_transactions(
        orders, dividends, transactions
    )
    assert len(all_trans) == 3
    assert all(isinstance(t, Transaction) for t in all_trans)
