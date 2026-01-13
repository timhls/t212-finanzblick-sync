"""Factory for creating Transaction objects from Trading 212 API data"""

from datetime import datetime
from typing import List, Dict
from ..models import Transaction, TransactionType


class TransactionFactory:
    """Creates Transaction objects from Trading 212 API responses"""
    
    @staticmethod
    def from_order(order: Dict) -> Transaction:
        """
        Create a Transaction from a Trading 212 order.
        
        Args:
            order: Order dictionary from Trading 212 API
            
        Returns:
            Transaction object
        """
        date = TransactionFactory._parse_date(order.get("dateCreated"))
        ticker = order.get("ticker", "Unknown")
        quantity = float(order.get("filledQuantity", 0))
        price = float(order.get("fillPrice", 0))
        direction = order.get("direction")  # BUY or SELL
        
        total_amount = quantity * price
        transaction_type = (
            TransactionType.BUY if direction == "BUY" 
            else TransactionType.SELL
        )
        
        description = f"Order {ticker} {quantity} Stk @ {price}"
        
        return Transaction(
            date=date,
            transaction_type=transaction_type,
            amount=total_amount,
            description=description,
            recipient="Trading 212 Markets",
            ticker=ticker,
            quantity=quantity,
            price=price
        )
    
    @staticmethod
    def from_dividend(dividend: Dict) -> Transaction:
        """
        Create a Transaction from a Trading 212 dividend.
        
        Args:
            dividend: Dividend dictionary from Trading 212 API
            
        Returns:
            Transaction object
        """
        date = TransactionFactory._parse_date(dividend.get("paidOn"))
        amount = float(dividend.get("amount", 0))
        ticker = dividend.get("ticker", "DIV")
        
        description = f"Dividende {ticker}"
        
        return Transaction(
            date=date,
            transaction_type=TransactionType.DIVIDEND,
            amount=amount,
            description=description,
            recipient="Trading 212 (Dividende)",
            ticker=ticker
        )
    
    @staticmethod
    def from_transaction(transaction: Dict) -> Transaction:
        """
        Create a Transaction from a Trading 212 cash transaction.
        
        Args:
            transaction: Transaction dictionary from Trading 212 API
            
        Returns:
            Transaction object
        """
        date = TransactionFactory._parse_date(transaction.get("date"))
        amount = float(transaction.get("amount", 0))
        type_str = transaction.get("type")  # DEPOSIT, WITHDRAWAL, INTEREST, etc.
        
        # Map transaction type
        type_mapping = {
            "DEPOSIT": (TransactionType.DEPOSIT, "Einzahlung auf Verrechnungskonto"),
            "WITHDRAWAL": (TransactionType.WITHDRAWAL, "Abhebung oder Kartenzahlung"),
            "INTEREST": (TransactionType.INTEREST, "Zinsen auf Guthaben"),
        }
        
        transaction_type, description = type_mapping.get(
            type_str,
            (TransactionType.OTHER, "Transaktion")
        )
        
        return Transaction(
            date=date,
            transaction_type=transaction_type,
            amount=abs(amount),
            description=description,
            recipient="Trading 212 Cash"
        )
    
    @staticmethod
    def _parse_date(iso_date_str: str) -> datetime:
        """
        Parse ISO date string to datetime object.
        
        Args:
            iso_date_str: ISO format date string
            
        Returns:
            datetime object
        """
        try:
            # Remove milliseconds and Z suffix
            clean_date = iso_date_str.split(".")[0].replace("Z", "")
            return datetime.fromisoformat(clean_date)
        except Exception:
            # Fallback to current time if parsing fails
            return datetime.now()
    
    @classmethod
    def create_all_transactions(
        cls,
        orders: List[Dict],
        dividends: List[Dict],
        transactions: List[Dict]
    ) -> List[Transaction]:
        """
        Create Transaction objects from all Trading 212 data.
        
        Args:
            orders: List of order dictionaries
            dividends: List of dividend dictionaries
            transactions: List of transaction dictionaries
            
        Returns:
            List of all Transaction objects
        """
        all_transactions = []
        
        # Process orders (only FILLED ones)
        for order in orders:
            if order.get("status") == "FILLED":
                all_transactions.append(cls.from_order(order))
        
        # Process dividends
        for dividend in dividends:
            all_transactions.append(cls.from_dividend(dividend))
        
        # Process cash transactions
        for transaction in transactions:
            all_transactions.append(cls.from_transaction(transaction))
        
        return all_transactions
