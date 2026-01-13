import requests
import pandas as pd
from datetime import datetime
import time
import os
import sys
import getpass
from pathlib import Path
from pykeepass import PyKeePass

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

# KeePass Integration

def load_keepass_config(config_path=".keeenv"):
    """
    Load KeePass configuration from .keeenv file.
    Returns a dict with 'database', 'keyfile' (optional), and 'env' mapping.
    """
    config = {"database": None, "keyfile": None, "env": {}}
    
    if not Path(config_path).exists():
        return None
    
    current_section = None
    with open(config_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1]
                continue
            
            if '=' not in line:
                continue
            
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            if current_section == 'keepass':
                if key == 'database':
                    config['database'] = value
                elif key == 'keyfile':
                    config['keyfile'] = value
            elif current_section == 'env':
                config['env'][key] = value
    
    return config if config['database'] else None


def parse_keepass_placeholder(placeholder):
    """
    Parse KeePass placeholder like ${"Entry Title".Password} or ${"Group/Entry"."API Key"}
    Returns tuple of (entry_path, attribute_name)
    """
    if not placeholder.startswith('${') or not placeholder.endswith('}'):
        return None, None
    
    inner = placeholder[2:-1].strip()
    
    # Split by last dot that's outside quotes
    parts = []
    current = ""
    in_quotes = False
    
    for char in inner:
        if char == '"':
            in_quotes = not in_quotes
        elif char == '.' and not in_quotes:
            parts.append(current.strip(' "'))
            current = ""
            continue
        current += char
    
    if current:
        parts.append(current.strip(' "'))
    
    if len(parts) == 2:
        return parts[0], parts[1]
    
    return None, None


def load_keepass_secrets(config):
    """
    Load secrets from KeePass database and set them as environment variables.
    """
    if not config or not config['database']:
        return False
    
    db_path = config['database']
    keyfile_path = config.get('keyfile')
    
    if not Path(db_path).exists():
        print(f"Error: KeePass database not found at {db_path}")
        return False
    
    # Prompt for password
    password = getpass.getpass(f"Enter KeePass password for {db_path}: ")
    
    try:
        # Open KeePass database
        kp = PyKeePass(db_path, password=password, keyfile=keyfile_path)
        
        # Process environment variable mappings
        for env_var, placeholder in config['env'].items():
            entry_path, attribute = parse_keepass_placeholder(placeholder)
            
            if not entry_path or not attribute:
                print(f"Warning: Could not parse placeholder for {env_var}: {placeholder}")
                continue
            
            # Handle group paths (e.g., "Group/Subgroup/Entry")
            path_parts = entry_path.split('/')
            entry_title = path_parts[-1]
            group_path = path_parts[:-1] if len(path_parts) > 1 else None
            
            # Find the entry
            if group_path:
                # Navigate to the specific group
                group = kp.root_group
                for group_name in group_path:
                    found_group = None
                    for subgroup in group.subgroups:
                        if subgroup.name == group_name:
                            found_group = subgroup
                            break
                    if not found_group:
                        print(f"Warning: Group '{group_name}' not found for {env_var}")
                        break
                    group = found_group
                else:
                    # Find entry in the found group
                    entry = kp.find_entries(title=entry_title, group=group, first=True)
            else:
                # Find entry in root
                entry = kp.find_entries(title=entry_title, first=True)
            
            if not entry:
                print(f"Warning: Entry '{entry_title}' not found for {env_var}")
                continue
            
            # Get the attribute value
            value = None
            if attribute.lower() == 'username':
                value = entry.username
            elif attribute.lower() == 'password':
                value = entry.password
            elif attribute.lower() == 'url':
                value = entry.url
            elif attribute.lower() == 'notes':
                value = entry.notes
            else:
                # Custom attribute
                value = entry.get_custom_property(attribute)
            
            if value:
                os.environ[env_var] = value
                print(f"Loaded {env_var} from KeePass")
            else:
                print(f"Warning: No value found for {env_var}.{attribute}")
        
        return True
        
    except Exception as e:
        print(f"Error loading KeePass database: {e}")
        return False


# Main Logic

def main():
    # Try to load secrets from KeePass if .keeenv exists
    config = load_keepass_config(".keeenv")
    if config:
        print("Found .keeenv configuration, loading secrets from KeePass...")
        if not load_keepass_secrets(config):
            print("Failed to load secrets from KeePass, exiting.")
            return
        # Reload API_KEY after setting environment variables
        global API_KEY
        API_KEY = os.getenv("T212_API_KEY")
    
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