
#!/usr/bin/env python3
"""
🚀 LuxOS System - Unified Entry Point
Wszystkie komponenty systemu LuxOS używają tego samego punktu wejścia
"""

import sys
from pathlib import Path

# Dodaj główny katalog do ścieżki Python
sys.path.insert(0, str(Path(__file__).parent))

# Import i uruchom główny system
from start import main

if __name__ == "__main__":
    print("🔄 Przekierowanie do unified LuxOS start system...")
    main()
