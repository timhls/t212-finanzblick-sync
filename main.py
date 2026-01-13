#!/usr/bin/env python3
"""Entry point for Trading 212 to Finanzblick sync"""

import sys
from src.app import Trading212SyncApp


def main():
    """Main entry point"""
    app = Trading212SyncApp()
    exit_code = app.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
