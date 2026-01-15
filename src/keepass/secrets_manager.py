"""KeePass secrets management"""

import os
import getpass
from pathlib import Path
from typing import Optional, Tuple
from pykeepass import PyKeePass  # type: ignore


class KeePassSecretsManager:
    """Manages loading secrets from KeePass database"""
    
    def __init__(self):
        self.kp: Optional[PyKeePass] = None
    
    def get_credentials(self) -> Optional[Tuple[str, str]]:
        """
        Load credentials from KeePass.
        
        Requires environment variables:
        - KEEPASS_DB_PATH: Path to KeePass database file
        - KEEPASS_ENTRY_TITLE: Name of the KeePass entry containing credentials
        
        Returns:
            Tuple of (api_key, api_secret), or None if loading failed
        """
        # Get environment variables
        db_path = os.getenv('KEEPASS_DB_PATH')
        entry_title = os.getenv('KEEPASS_ENTRY_TITLE')
        
        if not db_path or not entry_title:
            print("Error: KEEPASS_DB_PATH and KEEPASS_ENTRY_TITLE environment variables must be set")
            return None
        
        if not Path(db_path).exists():
            print(f"Error: KeePass database not found at {db_path}")
            return None
        
        # Prompt for password
        password = getpass.getpass(f"Enter KeePass password for {db_path}: ")
        
        try:
            # Open KeePass database
            self.kp = PyKeePass(db_path, password=password)
            
            # Find the entry
            entry = self._find_entry(entry_title)
            if not entry:
                print(f"Error: Entry '{entry_title}' not found in KeePass database")
                return None
            
            # Read credentials from username and password fields
            api_key = entry.username
            api_secret = entry.password
            
            if not api_key or not api_secret:
                print("Error: Entry must have both username (api_key) and password (api_secret) fields")
                return None
            
            print(f"Successfully loaded credentials from KeePass entry '{entry_title}'")
            return (api_key, api_secret)
            
        except Exception as e:
            print(f"Error loading KeePass database: {e}")
            return None
    
    def _find_entry(self, entry_title: str):
        """Find a KeePass entry by name (supports groups)"""
        if not self.kp:
            return None
        
        # Handle group paths (e.g., "Group/Subgroup/Entry")
        path_parts = entry_title.split('/')
        entry_title = path_parts[-1]
        group_path = path_parts[:-1] if len(path_parts) > 1 else None
        
        # Find the entry
        if group_path:
            # Navigate to the specific group
            group = self.kp.root_group
            for group_name in group_path:
                found_group = None
                for subgroup in group.subgroups:
                    if subgroup.name == group_name:
                        found_group = subgroup
                        break
                if not found_group:
                    print(f"Warning: Group '{group_name}' not found")
                    return None
                group = found_group
            
            # Find entry in the found group
            return self.kp.find_entries(title=entry_title, group=group, first=True)
        else:
            # Find entry in root
            return self.kp.find_entries(title=entry_title, first=True)
