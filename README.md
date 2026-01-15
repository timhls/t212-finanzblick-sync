# Trading 212 to Finanzblick Sync

This application synchronizes your Trading 212 transactions with Finanzblick by fetching data from the Trading 212 API and generating a CSV file in the format required by Finanzblick.

## Features

- 🔄 Fetches orders (buy/sell), dividends, and cash transactions from Trading 212
- 📊 Converts data to German CSV format (semicolon separator, comma decimal separator)
- 🔐 Secure credential management using KeePass integration
- 🏗️ Object-oriented architecture with clean separation of concerns
- 📦 Modular design for easy maintenance and extension

## Architecture

The application is structured using object-oriented design patterns:

- **`src/models/`** - Data models (Transaction, TransactionType)
- **`src/keepass/`** - KeePass integration for secure credential management
- **`src/trading212/`** - Trading 212 API client and transaction factory
- **`src/exporters/`** - Data exporters (Finanzblick CSV)
- **`src/app.py`** - Main application orchestrator
- **`main.py`** - Entry point

## Setup

### 1. Install dependencies

```bash
uv sync
```

or with pip:

```bash
pip install -r requirements.txt
```

### 2. Configure KeePass

The application loads Trading 212 credentials from a KeePass database for secure credential management.

1. Set the following environment variables:

```bash
export KEEPASS_DB_PATH="/path/to/your/database.kdbx"
export KEEPASS_ENTRY_TITLE="Trading212"
```

2. In your KeePass database, create an entry with the name specified in `KEEPASS_ENTRY_TITLE` and store your credentials:
   - **Username field**: Your Trading 212 API key
   - **Password field**: Your Trading 212 API secret

3. Run the application - it will prompt you for your KeePass password:

```bash
python main.py
```

The application will:
- Open the KeePass database at the specified path
- Find the entry by name (supports group paths like `"Finance/Trading212"`)
- Read the API key from the username field
- Read the API secret from the password field
- Create a Basic authentication header using base64 encoding

### Example

For a KeePass entry in a nested group:

```bash
export KEEPASS_DB_PATH="$HOME/secrets/passwords.kdbx"
export KEEPASS_ENTRY_TITLE="Finance/Trading212/API"
python main.py
```

## Output

The script generates `finanzblick_import_trading212.csv` which can be imported directly into Finanzblick.
