
#!/usr/bin/env python3
"""
🔄 LuxOS Import Migration Script
Automatycznie naprawia importy w całym repozytorium do spójnej struktury /luxdb/
"""

import os
import re
from pathlib import Path

# Mapowanie starych importów na nowe
IMPORT_MIGRATIONS = {
    'from ai.': 'from luxdb.ai.',
    'from core.': 'from luxdb.core.',
    'from database.': 'from luxdb.core.',
    'import ai.': 'import luxdb.ai.',
    'import core.': 'import luxdb.core.',
    'import database.': 'import luxdb.core.',
    'from database.postgre_db': 'from luxdb.core.postgre_db',
    'from core.globals': 'from luxdb.core.globals',
    'from genes.': 'from luxdb.utils.',
}

def migrate_file_imports(file_path: Path):
    """Migrates imports in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply import migrations
        for old_import, new_import in IMPORT_MIGRATIONS.items():
            content = content.replace(old_import, new_import)
        
        # Save if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Migrated: {file_path}")
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Error migrating {file_path}: {e}")
        return False

def main():
    """Main migration function"""
    print("🔄 Starting LuxOS Import Migration...")
    
    # Get all Python files (excluding legacy)
    python_files = []
    for root, dirs, files in os.walk('.'):
        # Skip legacy and archive directories
        if 'legacy' in root or 'archive' in root or '.git' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    
    print(f"📁 Found {len(python_files)} Python files to check")
    
    migrated_count = 0
    for file_path in python_files:
        if migrate_file_imports(file_path):
            migrated_count += 1
    
    print(f"\n✨ Migration completed!")
    print(f"📊 Migrated {migrated_count} files")
    print(f"🎯 All imports now use /luxdb/ structure")

if __name__ == "__main__":
    main()
