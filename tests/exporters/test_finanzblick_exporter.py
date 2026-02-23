from unittest.mock import patch

import pandas as pd

from src.exporters.finanzblick_exporter import FinanzblickCSVExporter
from src.models.transaction import Transaction, TransactionType


def test_format_german_number():
    assert FinanzblickCSVExporter._format_german_number(123.45) == "123,45"
    assert FinanzblickCSVExporter._format_german_number(-10.0) == "-10,00"
    assert FinanzblickCSVExporter._format_german_number(0) == "0,00"


def test_export_success():
    transactions = [
        Transaction(
            transaction_type=TransactionType.BUY,
            amount=-100,
            date=pd.Timestamp("2023-01-01"),
            description="Buy AAPL",
            recipient="Test Recipient",
        )
    ]

    exporter = FinanzblickCSVExporter("test.csv")
    with patch("pandas.DataFrame.to_csv") as mock_to_csv:
        success = exporter.export(transactions)

    assert success is True
    mock_to_csv.assert_called_once_with(
        "test.csv", index=False, sep=";", encoding="utf-8-sig"
    )


def test_export_no_transactions():
    exporter = FinanzblickCSVExporter()
    success = exporter.export([])
    assert success is False
