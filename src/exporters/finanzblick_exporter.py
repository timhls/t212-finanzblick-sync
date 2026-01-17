"""Finanzblick CSV exporter"""

from typing import List

import pandas as pd

from ..models import Transaction


class FinanzblickCSVExporter:
    """Exports transactions to Finanzblick CSV format"""

    # Column order required by Finanzblick
    COLUMNS = [
        "Buchungsdatum",
        "Wertstellungsdatum",
        "Auswertungsdatum",
        "Empfänger",
        "Verwendungszweck",
        "Buchungstext",
        "Betrag",
        "IBAN",
        "BIC",
    ]

    def __init__(self, output_filename: str = "finanzblick_import_trading212.csv"):
        """
        Initialize Finanzblick CSV exporter.

        Args:
            output_filename: Name of the output CSV file
        """
        self.output_filename = output_filename

    def export(self, transactions: List[Transaction]) -> bool:
        """
        Export transactions to Finanzblick CSV format.

        Args:
            transactions: List of Transaction objects to export

        Returns:
            True if export was successful, False otherwise
        """
        if not transactions:
            print("No transactions to export.")
            return False

        # Convert transactions to DataFrame
        rows = [t.to_finanzblick_row() for t in transactions]
        df = pd.DataFrame(rows)

        # Sort by date (most recent first)
        df["temp_date"] = pd.to_datetime(df["Buchungsdatum"], format="%d.%m.%Y")
        df = df.sort_values(by="temp_date", ascending=False)
        df = df.drop(columns=["temp_date"])

        # Ensure all columns exist and are in the correct order
        for col in self.COLUMNS:
            if col not in df.columns:
                df[col] = ""
        df = df[self.COLUMNS]

        # Format amount for German CSV (comma as decimal separator)
        df["Betrag"] = df["Betrag"].apply(self._format_german_number)

        # Export to CSV with German format
        # - Semicolon separator
        # - UTF-8 with BOM encoding
        df.to_csv(self.output_filename, index=False, sep=";", encoding="utf-8-sig")

        print(f"\nSuccess! File '{self.output_filename}' has been created.")
        print(f"Number of transactions: {len(df)}")
        print("You can now import this file into Finanzblick.")

        return True

    @staticmethod
    def _format_german_number(value: float) -> str:
        """
        Format a number for German CSV format.

        Args:
            value: Number to format

        Returns:
            String with comma as decimal separator
        """
        return "{:.2f}".format(value).replace(".", ",")
