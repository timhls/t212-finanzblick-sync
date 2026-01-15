"""Trading 212 API client"""

import base64
import time
from typing import List, Dict, Optional
import requests


class Trading212APIClient:
    """Client for Trading 212 API"""
    
    BASE_URL = "https://live.trading212.com/api/v0"
    RATE_LIMIT_DELAY = 0.2  # seconds between requests
    DEFAULT_PAGE_SIZE = 50
    
    def __init__(self, api_key: str, api_secret: str):
        """
        Initialize Trading 212 API client.
        
        Args:
            api_key: Trading 212 API key
            api_secret: Trading 212 API secret
        """
        # Create Basic auth header
        credentials_string = f"{api_key}:{api_secret}"
        encoded_credentials = base64.b64encode(credentials_string.encode('utf-8')).decode('utf-8')
        auth_header = f"Basic {encoded_credentials}"
        self.headers = {"Authorization": auth_header}
    
    def fetch_orders(self) -> List[Dict]:
        """
        Fetch all orders (buy/sell) from Trading 212.
        
        Returns:
            List of order dictionaries
        """
        return self._fetch_paginated("/equity/history/orders")
    
    def fetch_dividends(self) -> List[Dict]:
        """
        Fetch all dividend payments from Trading 212.
        
        Returns:
            List of dividend dictionaries
        """
        return self._fetch_paginated("/history/dividends")
    
    def fetch_transactions(self) -> List[Dict]:
        """
        Fetch all cash transactions (deposits, withdrawals, etc.) from Trading 212.
        
        Returns:
            List of transaction dictionaries
        """
        return self._fetch_paginated("/history/transactions")
    
    def _fetch_paginated(self, endpoint: str) -> List[Dict]:
        """
        Fetch all items from a paginated endpoint.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            List of all items from all pages
        """
        items = []
        cursor = None
        
        print(f"Fetching data from: {endpoint} ...")
        
        while True:
            params = {"limit": self.DEFAULT_PAGE_SIZE}
            if cursor:
                params["cursor"] = cursor
            
            try:
                response = requests.get(
                    f"{self.BASE_URL}{endpoint}",
                    headers=self.headers,
                    params=params
                )
                
                # Respect rate limiting
                time.sleep(self.RATE_LIMIT_DELAY)
                
                if response.status_code != 200:
                    print(f"Error fetching data: {response.status_code} - {response.text}")
                    break
                
                data = response.json()
                current_items = data.get("items", [])
                items.extend(current_items)
                
                # Check for next page cursor
                cursor = data.get("nextPagePath") or data.get("next")
                
                if not cursor:
                    break
                
            except Exception as e:
                print(f"Critical error during request: {e}")
                break
        
        print(f"-> {len(items)} entries found.")
        return items
