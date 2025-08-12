
#!/usr/bin/env python3
"""
Legacy database __init__.py - moved to legacy folder
"""

print("⚠️ Using legacy database module - migrate to luxdb.core")

# Legacy compatibility imports
try:
    from luxdb.core.postgre_db import Postgre_db
    from luxdb.repository.soul_repository import SoulRepository, BeingRepository
    print("✅ Legacy database compatibility layer loaded")
except ImportError as e:
    print(f"❌ Error loading legacy database compatibility: {e}")
