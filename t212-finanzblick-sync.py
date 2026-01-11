import requests
import pandas as pd
from datetime import datetime
import time
import os

# Configuration
# Insert your Trading 212 API Key as environment variable T212_API_KEY
API_KEY = os.getenv("T212_API_KEY")

# Base URL for the Trading 212 API
BASE_URL = "https://live.trading212.com/api/v0"

# Headers for requests
HEADERS = {
    "Authorization": API_KEY
}

# Helper Functions

def fetch_all_items(endpoint):
    """
    Fetches all items from an endpoint and handles pagination (cursor).
    """
    items = []
    cursor = None
    
    print(f"Fetching data from: {endpoint} ...")
    
    while True:
        params = {"limit": 50}
        if cursor:
            params["cursor"] = cursor
            
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=HEADERS, params=params)
            
            # Respect rate limiting (simple protection)
            time.sleep(0.2) 
            
            if response.status_code != 200:
                print(f"Error fetching data: {response.status_code} - {response.text}")
                break
                
            data = response.json()
            current_items = data.get("items", [])
            items.extend(current_items)
            
            cursor = data.get("nextPagePath") # Some endpoints use nextPagePath
            if not cursor:
                # Try via 'next' cursor token if nextPagePath is empty
                cursor = data.get("next")
            
            if not cursor:
                break
                
        except Exception as e:
            print(f"Critical error during request: {e}")
            break
            
    print(f"-> {len(items)} entries found.")
    return items

def format_date(iso_date_str):
    """
    Converts ISO date (2023-01-01T12:00:00Z) to German format (01.01.2023).
    """
    try:
        # Cut off milliseconds if present and parse
        clean_date = iso_date_str.split(".")[0].replace("Z", "")
        dt = datetime.fromisoformat(clean_date)
        return dt.strftime("%d.%m.%Y")
    except:
        return ""

def clean_number(value):
    """
    Ensures we have a float.
    """
    try:
        return float(value)
    except:
        return 0.0

# Main Logic

def main():
    if not API_KEY:
        print("ATTENTION: Please set the T212_API_KEY environment variable!")
        return

    all_rows = []

    # 1. Fetch Orders (Stock/ETF Buys & Sells)
    orders = fetch_all_items("/equity/history/orders")
    
    for order in orders:
        # Only consider filled orders
        if order.get("status") != "FILLED":
            continue
            
        date_str = format_date(order.get("dateCreated"))
        ticker = order.get("ticker", "Unknown")
        quantity = order.get("filledQuantity", 0)
        price = order.get("fillPrice", 0)
        
        # Calculate total amount of the order
        total_amount = float(quantity) * float(price)
        
        direction = order.get("direction") # BUY or SELL
        
        # Logic: Buy = Negative, Sell = Positive
        final_amount = 0.0
        buchungstext = ""
        
        if direction == "BUY":
            final_amount = -abs(total_amount)
            buchungstext = "Wertpapierkauf"
        elif direction == "SELL":
            final_amount = abs(total_amount)
            buchungstext = "Wertpapierverkauf"
            
        row = {
            "Buchungsdatum": date_str,
            "Wertstellungsdatum": date_str, # T212 settles almost immediately cash-wise for display
            "Auswertungsdatum": date_str,
            "Empfänger": "Trading 212 Markets",
            "Verwendungszweck": f"Order {ticker} {quantity} Stk @ {price}",
            "Buchungstext": buchungstext,
            "Betrag": final_amount,
            "IBAN": "", # No counter-IBAN for trades
            "BIC": ""
        }
        all_rows.append(row)

    # 2. Fetch Dividends
    dividends = fetch_all_items("/history/dividends")
    
    for div in dividends:
        date_str = format_date(div.get("paidOn"))
        amount = div.get("amount", 0)
        ticker = div.get("ticker", "DIV")
        
        # Dividenden are always positive
        final_amount = abs(float(amount))
        
        row = {
            "Buchungsdatum": date_str,
            "Wertstellungsdatum": date_str,
            "Auswertungsdatum": date_str,
            "Empfänger": "Trading 212 (Dividende)",
            "Verwendungszweck": f"Dividende {ticker}",
            "Buchungstext": "Dividende",
            "Betrag": final_amount,
            "IBAN": "",
            "BIC": ""
        }
        all_rows.append(row)

    # 3. Transactions (Deposits / Withdrawals / Card payments)
    # Note: The API often groups cash movements here.
    # Specific card details are sometimes limited in the API but appear as WITHDRAWAL.
    transactions = fetch_all_items("/history/transactions")
    
    for trans in transactions:
        date_str = format_date(trans.get("date"))
        amount = float(trans.get("amount", 0))
        type_trans = trans.get("type") # DEPOSIT, WITHDRAWAL, INTEREST, CARD etc.
        
        final_amount = 0.0
        buchungstext = "Sonstiges"
        zweck = "Transaktion"
        
        # Apply logic
        if type_trans == "DEPOSIT":
            final_amount = abs(amount) # Positive
            buchungstext = "Einlage"
            zweck = "Einzahlung auf Verrechnungskonto"
            
        elif type_trans == "WITHDRAWAL":
            final_amount = -abs(amount) # Negative
            buchungstext = "Auszahlung / Kartennutzung"
            zweck = "Abhebung oder Kartenzahlung"
            
        elif type_trans == "INTEREST":
            final_amount = abs(amount)
            buchungstext = "Zinsen"
            zweck = "Zinsen auf Guthaben"
            
        else:
            # Fallback for other types
            final_amount = amount
            buchungstext = type_trans
        
        row = {
            "Buchungsdatum": date_str,
            "Wertstellungsdatum": date_str,
            "Auswertungsdatum": date_str,
            "Empfänger": "Trading 212 Cash",
            "Verwendungszweck": zweck,
            "Buchungstext": buchungstext,
            "Betrag": final_amount,
            "IBAN": "",
            "BIC": ""
        }
        all_rows.append(row)

    # CSV Creation for Finanzblick
    if not all_rows:
        print("No data found or API error.")
        return

    df = pd.DataFrame(all_rows)
    
    # Sort by date
    # We need to temporarily parse the date for sorting as it is a string
    df['temp_date'] = pd.to_datetime(df['Buchungsdatum'], format="%d.%m.%Y")
    df = df.sort_values(by='temp_date', ascending=False)
    df = df.drop(columns=['temp_date'])
    
    # Ensure column order is exact
    cols = ["Buchungsdatum", "Wertstellungsdatum", "Auswertungsdatum", 
            "Empfänger", "Verwendungszweck", "Buchungstext", 
            "Betrag", "IBAN", "BIC"]
    
    # Fill missing columns (if skipped in logic above)
    for c in cols:
        if c not in df.columns:
            df[c] = ""

    df = df[cols]

    # IMPORTANT FOR FINANZBLICK / GERMAN CSVs:
    # 1. Separator is semicolon (;)
    # 2. Decimal separator is comma (,)
    
    # Convert floats to German format string
    # We format to 2 decimal places
    df['Betrag'] = df['Betrag'].apply(lambda x: "{:.2f}".format(x).replace(".", ","))

    filename = "finanzblick_import_trading212.csv"
    df.to_csv(filename, index=False, sep=";", encoding="utf-8-sig")
    
    print(f"\nSuccess! File '{filename}' has been created.")
    print(f"Number of transactions: {len(df)}")
    print("You can now import this file into Finanzblick.")

if __name__ == "__main__":
    main()