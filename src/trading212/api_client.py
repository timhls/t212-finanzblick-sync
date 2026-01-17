"""Trading 212 API client"""

import base64
import time
from typing import Dict, List

import requests
from tqdm import tqdm


class Trading212APIClient:
    """Client for Trading 212 API"""

    BASE_URL = "https://live.trading212.com"
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
        encoded_credentials = base64.b64encode(
            credentials_string.encode("utf-8")
        ).decode("utf-8")
        auth_header = f"Basic {encoded_credentials}"
        self.headers = {"Authorization": auth_header}

    def fetch_orders(self) -> List[Dict]:
        """
        Fetch all orders (buy/sell) from Trading 212.

        Returns:
            List of order dictionaries
        """
        return self._fetch_paginated("/api/v0/equity/history/orders")

    def fetch_dividends(self) -> List[Dict]:
        """
        Fetch all dividend payments from Trading 212.

        Returns:
            List of dividend dictionaries
        """
        return self._fetch_paginated("/api/v0/history/dividends")

    def fetch_transactions(self) -> List[Dict]:
        """
        Fetch all cash transactions (deposits, withdrawals, etc.) from Trading 212.

        Returns:
            List of transaction dictionaries
        """
        return self._fetch_paginated("/api/v0/history/transactions")

    def _fetch_paginated(self, endpoint: str) -> List[Dict]:
        """
        Fetch all items from a paginated endpoint.

        Args:
            endpoint: API endpoint path

        Returns:
            List of all items from all pages
        """
        items = []
        next_page_path = f"{endpoint}?limit={self.DEFAULT_PAGE_SIZE}"

        print(f"Fetching data from: {endpoint} ...")

        with tqdm(unit="items") as pbar:
            while next_page_path:
                try:
                    # nextPagePath already includes /api/v0, so use BASE_URL instead
                    url = f"{self.BASE_URL}{next_page_path}"
                    response = requests.get(url, headers=self.headers)

                    # Respect rate limiting
                    time.sleep(self.RATE_LIMIT_DELAY)

                    if response.status_code != 200:
                        print(
                            f"Error fetching data: {response.status_code} - "
                            f"{response.text}"
                        )
                        break

                    data = response.json()
                    current_items = data.get("items", [])
                    items.extend(current_items)

                    pbar.update(len(current_items))
                    pbar.set_description(f"Fetched {len(items)} items")

                    # Get the full path for the next page (includes limit and cursor)
                    next_page_path = data.get("nextPagePath")

                except Exception as e:
                    print(f"Critical error during request: {e}")
                    break

        print(f"-> {len(items)} entries found.")
        return items
