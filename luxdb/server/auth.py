
"""
Authentication Manager - Basic auth for LuxDB Server
"""

import hashlib
import secrets
from typing import Dict, Optional, Any
from datetime import datetime, timedelta


class AuthManager:
    """
    Basic authentication manager for LuxDB Server
    Prepares infrastructure for multi-user support
    """
    
    def __init__(self):
        self.users: Dict[str, Dict[str, Any]] = {}
        self.tokens: Dict[str, Dict[str, Any]] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def hash_password(self, password: str) -> str:
        """Hash password with salt"""
        salt = secrets.token_hex(32)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}:{password_hash.hex()}"
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            salt, hash_part = password_hash.split(':')
            password_check = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return password_check.hex() == hash_part
        except:
            return False
    
    def create_user(self, username: str, password: str, permissions: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create new user"""
        if username in self.users:
            raise ValueError(f"User {username} already exists")
        
        user_data = {
            "username": username,
            "password_hash": self.hash_password(password),
            "permissions": permissions or {"namespaces": ["*"]},
            "created_at": datetime.utcnow().isoformat(),
            "active": True
        }
        
        self.users[username] = user_data
        return {"username": username, "created": True}
    
    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        """Authenticate user and return token"""
        if username not in self.users:
            return None
        
        user = self.users[username]
        if not user["active"] or not self.verify_password(password, user["password_hash"]):
            return None
        
        # Generate token
        token = secrets.token_urlsafe(32)
        self.tokens[token] = {
            "username": username,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=24)
        }
        
        return token
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate token and return user info"""
        if token not in self.tokens:
            return None
        
        token_data = self.tokens[token]
        if datetime.utcnow() > token_data["expires_at"]:
            del self.tokens[token]
            return None
        
        username = token_data["username"]
        if username not in self.users:
            del self.tokens[token]
            return None
        
        return self.users[username]
    
    def check_namespace_permission(self, username: str, namespace_id: str) -> bool:
        """Check if user has permission to access namespace"""
        if username not in self.users:
            return False
        
        user = self.users[username]
        permissions = user.get("permissions", {})
        allowed_namespaces = permissions.get("namespaces", [])
        
        # Wildcard permission
        if "*" in allowed_namespaces:
            return True
        
        # Specific namespace permission
        return namespace_id in allowed_namespaces
    
    def revoke_token(self, token: str) -> bool:
        """Revoke token"""
        if token in self.tokens:
            del self.tokens[token]
            return True
        return False
    
    def cleanup_expired_tokens(self):
        """Remove expired tokens"""
        now = datetime.utcnow()
        expired_tokens = [
            token for token, data in self.tokens.items()
            if now > data["expires_at"]
        ]
        
        for token in expired_tokens:
            del self.tokens[token]
        
        return len(expired_tokens)
