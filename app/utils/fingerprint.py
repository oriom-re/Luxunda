
import hashlib
import json
from typing import Dict, Any

class FingerprintManager:
    """Menedżer fingerprintów dla identyfikacji klientów"""
    
    @staticmethod
    def generate_test_fingerprint() -> str:
        """Generuje testowy fingerprint dla rozwoju"""
        # Dla testów - zawsze ten sam fingerprint
        test_data = {
            'user_agent': 'LuxOS-TestBrowser/1.0',
            'screen_resolution': '1920x1080',
            'timezone': 'UTC+1',
            'language': 'pl-PL',
            'test_mode': True
        }
        
        fingerprint_string = json.dumps(test_data, sort_keys=True)
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()
    
    @staticmethod
    def generate_fingerprint_from_headers(headers: Dict[str, str]) -> str:
        """Generuje fingerprint z nagłówków HTTP"""
        relevant_headers = {
            'user-agent': headers.get('User-Agent', 'unknown'),
            'accept-language': headers.get('Accept-Language', 'unknown'),
            'accept-encoding': headers.get('Accept-Encoding', 'unknown'),
        }
        
        fingerprint_string = json.dumps(relevant_headers, sort_keys=True)
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()
    
    @staticmethod
    def generate_fingerprint_from_client_data(client_data: Dict[str, Any]) -> str:
        """Generuje fingerprint z danych klienta (przyszłościowo)"""
        # Wybierz kluczowe dane dla fingerprinta
        relevant_data = {
            'user_agent': client_data.get('userAgent', 'unknown'),
            'screen_resolution': f"{client_data.get('screenWidth', 0)}x{client_data.get('screenHeight', 0)}",
            'timezone': client_data.get('timezone', 'unknown'),
            'language': client_data.get('language', 'unknown'),
            'platform': client_data.get('platform', 'unknown')
        }
        
        fingerprint_string = json.dumps(relevant_data, sort_keys=True)
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()
