"""Main application orchestrator"""

from typing import Optional

from .exporters import FinanzblickCSVExporter
from .keepass import KeePassSecretsManager
from .trading212 import Trading212APIClient, TransactionFactory


class Trading212SyncApp:
    """Main application for syncing Trading 212 to Finanzblick"""

    def __init__(self):
        """
        Initialize the sync application.
        """
        self.credentials: Optional[tuple] = None

    def run(self) -> int:
        """
        Run the sync application.

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        # Load credentials from KeePass
        manager = KeePassSecretsManager()
        self.credentials = manager.get_credentials()

        if not self.credentials:
            print("Failed to load credentials from KeePass.")
            return 1

        # Fetch data from Trading 212
        print("\n=== Fetching data from Trading 212 ===")
        api_key, api_secret = self.credentials
        client = Trading212APIClient(api_key, api_secret)

        orders = client.fetch_orders()
        dividends = client.fetch_dividends()
        transactions = client.fetch_transactions()

        # Convert to Transaction objects
        print("\n=== Processing transactions ===")
        all_transactions = TransactionFactory.create_all_transactions(
            orders, dividends, transactions
        )

        if not all_transactions:
            print("No transactions found or API error.")
            return 1

        print(f"Processed {len(all_transactions)} transactions")

        # Export to Finanzblick CSV
        print("\n=== Exporting to Finanzblick format ===")
        exporter = FinanzblickCSVExporter()
        success = exporter.export(all_transactions)

        return 0 if success else 1
