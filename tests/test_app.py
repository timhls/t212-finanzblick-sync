from unittest.mock import MagicMock, patch

from src.app import Trading212SyncApp


@patch("src.app.FinanzblickCSVExporter")
@patch("src.app.TransactionFactory")
@patch("src.app.Trading212APIClient")
def test_run_success(mock_api_client, mock_factory, mock_exporter):
    mock_api_instance = MagicMock()
    mock_api_client.return_value = mock_api_instance
    mock_api_instance.fetch_orders.return_value = [{"id": 1}]
    mock_api_instance.fetch_dividends.return_value = []
    mock_api_instance.fetch_transactions.return_value = []

    mock_factory.create_all_transactions.return_value = [MagicMock()]

    mock_exporter_instance = MagicMock()
    mock_exporter.return_value = mock_exporter_instance
    mock_exporter_instance.export.return_value = True

    app = Trading212SyncApp()
    exit_code = app.run()

    assert exit_code == 0
    mock_api_instance.fetch_orders.assert_called_once()
    mock_factory.create_all_transactions.assert_called_once()
    mock_exporter_instance.export.assert_called_once()


@patch("src.app.Trading212APIClient", side_effect=Exception("API Error"))
def test_run_api_client_failure(mock_api_client):
    app = Trading212SyncApp()
    with patch("builtins.print") as mock_print:
        exit_code = app.run()

    assert exit_code == 1
    mock_print.assert_any_call("An unexpected error occurred: API Error")


@patch("src.app.FinanzblickCSVExporter")
@patch("src.app.TransactionFactory")
@patch("src.app.Trading212APIClient")
def test_run_no_transactions(mock_api_client, mock_factory, mock_exporter):
    mock_api_instance = MagicMock()
    mock_api_client.return_value = mock_api_instance
    mock_api_instance.fetch_orders.return_value = []
    mock_api_instance.fetch_dividends.return_value = []
    mock_api_instance.fetch_transactions.return_value = []

    mock_factory.create_all_transactions.return_value = []

    app = Trading212SyncApp()
    exit_code = app.run()

    assert exit_code == 1
