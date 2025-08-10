
"""
Deployment Manager - zarządza trybem development vs production
"""

import os
import json
from typing import Dict, Any, Optional
from enum import Enum

class DeploymentMode(Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    STAGING = "staging"

class DeploymentManager:
    """Zarządza konfiguracją deployment"""
    
    def __init__(self):
        self.mode = self._detect_mode()
        self.config = self._load_config()
    
    def _detect_mode(self) -> DeploymentMode:
        """Automatycznie wykrywa tryb deployment"""
        
        # Sprawdź zmienne środowiskowe
        env_mode = os.getenv('LUXDB_MODE', '').lower()
        if env_mode in ['production', 'prod']:
            return DeploymentMode.PRODUCTION
        elif env_mode in ['staging', 'stage']:
            return DeploymentMode.STAGING
        
        # Sprawdź czy to Replit deployment
        if os.getenv('REPL_DEPLOYMENT') or os.getenv('REPLIT_DEPLOYMENT'):
            return DeploymentMode.PRODUCTION
        
        # Default do development
        return DeploymentMode.DEVELOPMENT
    
    def _load_config(self) -> Dict[str, Any]:
        """Ładuje konfigurację dla danego trybu"""
        base_config = {
            'host': '0.0.0.0',
            'debug': False,
            'log_level': 'INFO',
            'max_connections': 100,
            'workspace_enabled': True,
            'discord_enabled': False
        }
        
        if self.mode == DeploymentMode.DEVELOPMENT:
            base_config.update({
                'port': 3001,
                'debug': True,
                'log_level': 'DEBUG',
                'hot_reload': True,
                'workspace_enabled': True,
                'discord_enabled': True
            })
        
        elif self.mode == DeploymentMode.PRODUCTION:
            base_config.update({
                'port': int(os.getenv('PORT', 5000)),
                'debug': False,
                'log_level': 'WARNING',
                'hot_reload': False,
                'max_connections': 1000,
                'workspace_enabled': False,  # Bezpieczeństwo w production
                'discord_enabled': bool(os.getenv('DISCORD_BOT_TOKEN'))
            })
        
        elif self.mode == DeploymentMode.STAGING:
            base_config.update({
                'port': int(os.getenv('PORT', 3001)),
                'debug': True,
                'log_level': 'INFO',
                'workspace_enabled': True,
                'discord_enabled': bool(os.getenv('DISCORD_BOT_TOKEN'))
            })
        
        return base_config
    
    def get_config(self, key: str = None) -> Any:
        """Pobiera konfigurację"""
        if key:
            return self.config.get(key)
        return self.config
    
    def is_production(self) -> bool:
        """Sprawdza czy to production"""
        return self.mode == DeploymentMode.PRODUCTION
    
    def is_development(self) -> bool:
        """Sprawdza czy to development"""
        return self.mode == DeploymentMode.DEVELOPMENT
    
    def get_database_config(self) -> Dict[str, Any]:
        """Konfiguracja bazy danych zależnie od trybu"""
        if self.is_production():
            return {
                'host': os.getenv('DATABASE_URL', 'localhost'),
                'port': int(os.getenv('DATABASE_PORT', 5432)),
                'database': os.getenv('DATABASE_NAME', 'luxdb_prod'),
                'user': os.getenv('DATABASE_USER', 'postgres'),
                'password': os.getenv('DATABASE_PASSWORD', ''),
                'ssl': True,
                'pool_size': 20
            }
        else:
            return {
                'host': 'localhost',
                'port': 5432,
                'database': 'luxdb_dev',
                'user': 'postgres',
                'password': 'password',
                'ssl': False,
                'pool_size': 5
            }
    
    def should_enable_feature(self, feature: str) -> bool:
        """Sprawdza czy feature powinien być włączony"""
        feature_map = {
            'workspace': self.config.get('workspace_enabled', False),
            'discord': self.config.get('discord_enabled', False),
            'hot_reload': self.config.get('hot_reload', False),
            'debug': self.config.get('debug', False)
        }
        
        return feature_map.get(feature, False)

# Globalna instancja
deployment_manager = DeploymentManager()
