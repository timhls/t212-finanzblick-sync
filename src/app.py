"""Main application orchestrator"""

import os
from typing import Optional
from .keepass import KeePassConfigLoader, KeePassSecretsManager
from .trading212 import Trading212APIClient, TransactionFactory
from .exporters import FinanzblickCSVExporter


class Trading212SyncApp:
    """Main application for syncing Trading 212 to Finanzblick"""
    
    def __init__(self, config_path: str = ".keeenv"):
        """
        Initialize the sync application.
        
        Args:
            config_path: Path to .keeenv configuration file
        """
        self.config_path = config_path
        self.api_key: Optional[str] = None
    
    def run(self) -> int:
        """
        Run the sync application.
        
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        # Load KeePass secrets if available
        if not self._load_secrets():
            print("Failed to load secrets.")
            return 1
        
        # Get API key from environment
        self.api_key = os.getenv("T212_API_KEY")
        if not self.api_key:
            print("ATTENTION: Please set the T212_API_KEY environment variable!")
            return 1
        
        # Fetch data from Trading 212
        print("\n=== Fetching data from Trading 212 ===")
        client = Trading212APIClient(self.api_key)
        
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
    
    def _load_secrets(self) -> bool:
        """
        Load secrets from KeePass if configuration exists.
        
        Returns:
            True if secrets loaded or no config found, False if loading failed
        """
        loader = KeePassConfigLoader(self.config_path)
        config = loader.load()
        
        if not config:
            # No .keeenv file found, user can use environment variables
            return True
        
        print("Found .keeenv configuration, loading secrets from KeePass...")
        manager = KeePassSecretsManager(config)
        return manager.load_secrets()
