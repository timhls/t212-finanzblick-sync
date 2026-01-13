"""KeePass secrets management"""

import os
import getpass
from pathlib import Path
from typing import Optional, Dict, Tuple
from pykeepass import PyKeePass


class KeePassSecretsManager:
    """Manages loading secrets from KeePass database"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.kp: Optional[PyKeePass] = None
    
    def load_secrets(self) -> bool:
        """
        Load secrets from KeePass database and set them as environment variables.
        
        Returns:
            True if secrets were loaded successfully, False otherwise
        """
        if not self.config or not self.config.get('database'):
            return False
        
        db_path = self.config['database']
        keyfile_path = self.config.get('keyfile')
        
        if not Path(db_path).exists():
            print(f"Error: KeePass database not found at {db_path}")
            return False
        
        # Prompt for password
        password = getpass.getpass(f"Enter KeePass password for {db_path}: ")
        
        try:
            # Open KeePass database
            self.kp = PyKeePass(db_path, password=password, keyfile=keyfile_path)
            
            # Process environment variable mappings
            for env_var, placeholder in self.config['env'].items():
                value = self._resolve_placeholder(env_var, placeholder)
                if value:
                    os.environ[env_var] = value
                    print(f"Loaded {env_var} from KeePass")
            
            return True
            
        except Exception as e:
            print(f"Error loading KeePass database: {e}")
            return False
    
    def _resolve_placeholder(self, env_var: str, placeholder: str) -> Optional[str]:
        """Resolve a KeePass placeholder to its value"""
        entry_path, attribute = self._parse_placeholder(placeholder)
        
        if not entry_path or not attribute:
            print(f"Warning: Could not parse placeholder for {env_var}: {placeholder}")
            return None
        
        entry = self._find_entry(entry_path)
        if not entry:
            print(f"Warning: Entry '{entry_path}' not found for {env_var}")
            return None
        
        return self._get_entry_attribute(entry, attribute, env_var)
    
    @staticmethod
    def _parse_placeholder(placeholder: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse KeePass placeholder like ${"Entry Title".Password} or ${"Group/Entry"."API Key"}
        
        Returns:
            Tuple of (entry_path, attribute_name)
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
    
    def _find_entry(self, entry_path: str):
        """Find a KeePass entry by path (supports groups)"""
        if not self.kp:
            return None
        
        # Handle group paths (e.g., "Group/Subgroup/Entry")
        path_parts = entry_path.split('/')
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
    
    @staticmethod
    def _get_entry_attribute(entry, attribute: str, env_var: str) -> Optional[str]:
        """Get a specific attribute from a KeePass entry"""
        value = None
        attribute_lower = attribute.lower()
        
        if attribute_lower == 'username':
            value = entry.username
        elif attribute_lower == 'password':
            value = entry.password
        elif attribute_lower == 'url':
            value = entry.url
        elif attribute_lower == 'notes':
            value = entry.notes
        else:
            # Custom attribute
            value = entry.get_custom_property(attribute)
        
        if not value:
            print(f"Warning: No value found for {env_var}.{attribute}")
        
        return value
