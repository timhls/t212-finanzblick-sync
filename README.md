# Trading 212 to Finanzblick Sync

This script synchronizes your Trading 212 transactions with Finanzblick by fetching data from the Trading 212 API and generating a CSV file in the format required by Finanzblick.

## Features

- Fetches orders (buy/sell), dividends, and cash transactions from Trading 212
- Converts data to German CSV format (semicolon separator, comma decimal separator)
- Secure credential management using KeePass integration

## Setup

### 1. Install dependencies

```bash
uv sync
```

or with pip:

```bash
pip install -r requirements.txt
```

### 2. Configure KeePass (Recommended)

The script supports loading your Trading 212 API key from a KeePass database for secure credential management.

1. Create a `.keeenv` file in the project root (you can copy `.keeenv.example`):

```ini
[keepass]
database = secrets.kdbx
keyfile = 

[env]
T212_API_KEY = ${"Trading 212".Password}
```

2. In your KeePass database, create an entry titled "Trading 212" and store your API key in the Password field (or customize the mapping in `.keeenv`).

3. Run the script - it will prompt you for your KeePass password:

```bash
python t212-finanzblick-sync.py
```

### Alternative: Environment Variable

If you prefer not to use KeePass, you can set the API key as an environment variable:

```bash
export T212_API_KEY="your-api-key-here"
python t212-finanzblick-sync.py
```

## KeePass Configuration

The `.keeenv` file uses the following format:

- **[keepass] section**: Defines the KeePass database location
  - `database`: Path to your `.kdbx` file
  - `keyfile`: (optional) Path to key file if you use one

- **[env] section**: Maps environment variables to KeePass entries
  - Format: `ENV_VAR = ${"Entry Title".Attribute}`
  - Standard attributes: `Username`, `Password`, `URL`, `Notes`
  - Custom attributes are also supported (use quotes if they contain spaces)

### Examples

Store API key in Password field:
```ini
T212_API_KEY = ${"Trading 212".Password}
```

Store in a custom attribute:
```ini
T212_API_KEY = ${"Trading 212"."API Key"}
```

Use grouped entries:
```ini
T212_API_KEY = ${"Finance/Trading212/API".Password}
```

## Output

The script generates `finanzblick_import_trading212.csv` which can be imported directly into Finanzblick.

## Credits

KeePass integration inspired by [keeenv](https://github.com/scross01/keeenv)
