
#!/usr/bin/env python3
"""
LuxOS Archive System - Archiwizacja nieużywanych komponentów
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

def create_archive():
    """Tworzy archiwum z nieużywanych komponentów"""
    
    archive_name = f"luxos_archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    archive_path = Path(archive_name)
    
    # Komponenty do archiwizacji
    to_archive = [
        "legacy",
        "examples", 
        "tests",
        "static",
        "scenarios",
        "raporty",
        "workspace",
        "ai",
        "clients",
        "core",
        "database",
        "gen_files",
        "genes",
        "luxdb",
        "services",
        
        # Pliki demo i alternatywne
        "demo_*.py",
        "luxos_frontend_server.py",
        "luxos_simple_system.py", 
        "luxos_single_app.py",
        "admin_kernel_server.py",
        "test_*.py",
        "hybrid_demo.py",
        "run_tests.py",
        
        # Dokumentacja i konfiguracje
        "documentation.md",
        "manifest.md",
        "LUXDB_MVP_SUMMARY.md",
        "DISCORD_SETUP.md",
        "STANDARD_DATA_FETCHING.md",
        "deployment.env.example",
        "fix_schema_mismatch.py",
        "database_cleanup.py"
    ]
    
    print(f"🗃️ Tworzenie archiwum: {archive_name}")
    archive_path.mkdir(exist_ok=True)
    
    archived_count = 0
    
    for item in to_archive:
        if "*" in item:
            # Obsługa wzorców
            import glob
            matches = glob.glob(item)
            for match in matches:
                if os.path.exists(match):
                    try:
                        if os.path.isdir(match):
                            shutil.move(match, archive_path / match)
                        else:
                            shutil.move(match, archive_path / match)
                        print(f"📦 Zarchiwizowano: {match}")
                        archived_count += 1
                    except Exception as e:
                        print(f"❌ Błąd archiwizacji {match}: {e}")
        else:
            if os.path.exists(item):
                try:
                    if os.path.isdir(item):
                        shutil.move(item, archive_path / item)
                    else:
                        shutil.move(item, archive_path / item)
                    print(f"📦 Zarchiwizowano: {item}")
                    archived_count += 1
                except Exception as e:
                    print(f"❌ Błąd archiwizacji {item}: {e}")
    
    # Utwórz README w archiwum
    readme_content = f"""# LuxOS Archive - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

To archiwum zawiera komponenty LuxOS przeniesione z głównego katalogu.

## Zarchiwizowane komponenty:
- Legacy code (legacy/)
- Przykłady (examples/)
- Testy (tests/)
- Interfejsy statyczne (static/)
- Scenariusze (scenarios/)
- Dokumentacja (documentation.md, manifest.md, itp.)
- Alternatywne serwery (luxos_frontend_server.py, luxos_simple_system.py)
- Narzędzia pomocnicze

## System główny:
Aktywny pozostaje tylko główny system w `main.py`.

Zarchiwizowano łącznie: {archived_count} elementów
"""
    
    with open(archive_path / "README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print(f"✅ Archiwizacja zakończona. Zarchiwizowano {archived_count} elementów do {archive_name}/")
    print(f"📋 System główny: main.py pozostaje aktywny")
    
    return archive_name

if __name__ == "__main__":
    archive_name = create_archive()
    print(f"\n🎯 Archiwum utworzone: {archive_name}")
    print("🚀 System gotowy - tylko main.py aktywny")
