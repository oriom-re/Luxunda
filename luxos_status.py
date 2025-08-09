
#!/usr/bin/env python3
"""
📊 LuxOS Status Checker - Sprawdzenie stanu systemu
"""

import sys
from pathlib import Path
from datetime import datetime
import requests

# Dodaj główny katalog do ścieżki Python
sys.path.insert(0, str(Path(__file__).parent))

def check_admin_interface():
    """Sprawdź czy Admin Interface jest dostępny"""
    try:
        response = requests.get("http://0.0.0.0:3030/api/system/status", timeout=5)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"HTTP {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Brak połączenia"
    except Exception as e:
        return False, str(e)

def main():
    """Sprawdź status systemu"""
    print("📊 LuxOS System Status Check")
    print("=" * 40)
    
    # Sprawdź Admin Interface
    admin_available, admin_data = check_admin_interface()
    
    if admin_available:
        print("✅ Admin Interface: AKTYWNY")
        print("🌐 URL: http://0.0.0.0:3030")
        
        if isinstance(admin_data, dict):
            print(f"🔧 Aktywne połączenia: {admin_data.get('admin_interface', {}).get('connections', 'N/A')}")
            print(f"📊 Zarejestrowane byty: {admin_data.get('kernel_system', {}).get('registered_beings', 'N/A')}")
            print(f"🧬 Załadowane hashe: {admin_data.get('kernel_system', {}).get('loaded_hashes', 'N/A')}")
    else:
        print("❌ Admin Interface: NIEAKTYWNY")
        print(f"🔍 Powód: {admin_data}")
        print("💡 Uruchom: python luxos_wake_up.py")
    
    print("\n🕐 Sprawdzenie wykonane:", datetime.now().isoformat())
    
    return admin_available

if __name__ == "__main__":
    main()
