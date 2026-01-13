"""KeePass configuration loader"""

from pathlib import Path
from typing import Optional, Dict


class KeePassConfigLoader:
    """Loads and parses .keeenv configuration files"""
    
    def __init__(self, config_path: str = ".keeenv"):
        self.config_path = Path(config_path)
        self._config: Optional[Dict] = None
    
    def load(self) -> Optional[Dict]:
        """
        Load KeePass configuration from .keeenv file.
        
        Returns:
            Dict with 'database', 'keyfile' (optional), and 'env' mapping,
            or None if config file doesn't exist or is invalid
        """
        if not self.config_path.exists():
            return None
        
        config = {"database": None, "keyfile": None, "env": {}}
        current_section = None
        
        with open(self.config_path, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse section headers
                if line.startswith('[') and line.endswith(']'):
                    current_section = line[1:-1]
                    continue
                
                # Parse key-value pairs
                if '=' not in line:
                    continue
                
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                if current_section == 'keepass':
                    if key == 'database':
                        config['database'] = value
                    elif key == 'keyfile':
                        config['keyfile'] = value if value else None
                elif current_section == 'env':
                    config['env'][key] = value
        
        self._config = config if config['database'] else None
        return self._config
    
    @property
    def config(self) -> Optional[Dict]:
        """Returns cached configuration"""
        return self._config
    
    @property
    def has_config(self) -> bool:
        """Check if a valid configuration was loaded"""
        return self._config is not None and self._config.get('database') is not None
