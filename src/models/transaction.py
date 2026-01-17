"""Transaction data models"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class TransactionType(Enum):
    """Types of transactions"""

    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    INTEREST = "interest"
    OTHER = "other"


@dataclass
class Transaction:
    """Represents a financial transaction"""

    date: datetime
    transaction_type: TransactionType
    amount: float
    description: str
    recipient: str
    ticker: Optional[str] = None
    quantity: Optional[float] = None
    price: Optional[float] = None

    @property
    def formatted_date(self) -> str:
        """Returns date in German format (DD.MM.YYYY)"""
        return self.date.strftime("%d.%m.%Y")

    @property
    def booking_text(self) -> str:
        """Returns the German booking text based on transaction type"""
        mapping = {
            TransactionType.BUY: "Wertpapierkauf",
            TransactionType.SELL: "Wertpapierverkauf",
            TransactionType.DIVIDEND: "Dividende",
            TransactionType.DEPOSIT: "Einlage",
            TransactionType.WITHDRAWAL: "Auszahlung / Kartennutzung",
            TransactionType.INTEREST: "Zinsen",
            TransactionType.OTHER: "Sonstiges",
        }
        return mapping.get(self.transaction_type, "Sonstiges")

    @property
    def signed_amount(self) -> float:
        """Returns amount with correct sign (negative for expenses)"""
        if self.transaction_type in [TransactionType.BUY, TransactionType.WITHDRAWAL]:
            return -abs(self.amount)
        return abs(self.amount)

    def to_finanzblick_row(self) -> dict:
        """Converts transaction to Finanzblick CSV row format"""
        return {
            "Buchungsdatum": self.formatted_date,
            "Wertstellungsdatum": self.formatted_date,
            "Auswertungsdatum": self.formatted_date,
            "Empfänger": self.recipient,
            "Verwendungszweck": self.description,
            "Buchungstext": self.booking_text,
            "Betrag": self.signed_amount,
            "IBAN": "",
            "BIC": "",
        }
