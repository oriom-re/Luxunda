
#!/usr/bin/env python3
"""
🎯 LuxOS Soul Management CLI - Narzędzie linii komend dla zarządzania duszami

Umożliwia zarządzanie hashami, promocję do produkcji i generowanie raportów.
"""

import asyncio
import argparse
from pathlib import Path
from luxdb.utils.soul_creation_logger import soul_creation_logger
from luxdb.utils.production_hash_manager import production_hash_manager
from luxdb.models.soul import Soul

class SoulManagerCLI:
    """CLI Manager dla operacji na Soul"""
    
    async def list_souls(self, alias: str = None):
        """Lista wszystkich souls lub dla konkretnego aliasu"""
        if alias:
            souls = soul_creation_logger.get_souls_by_alias(alias)
            if souls:
                print(f"📋 Souls for alias '{alias}':")
                for soul_info in souls:
                    print(f"  🧬 {soul_info['soul_hash'][:16]}... (v{soul_info['version']})")
            else:
                print(f"❌ No souls found for alias '{alias}'")
        else:
            index_path = Path("logs/souls/hash_index.json")
            if index_path.exists():
                import json
                with open(index_path) as f:
                    index = json.load(f)
                
                print(f"📋 All souls ({len(index['souls'])} total):")
                for hash_val, info in index['souls'].items():
                    print(f"  🧬 {hash_val[:16]}... - {info['alias']} (v{info['version']})")
            else:
                print("❌ No souls index found")
    
    async def show_soul(self, soul_hash: str):
        """Pokazuje szczegóły konkretnej Soul"""
        soul_info = soul_creation_logger.get_soul_by_hash(soul_hash)
        if soul_info:
            print(f"🧬 Soul Details:")
            print(f"  Hash: {soul_hash}")
            print(f"  Alias: {soul_info['alias']}")
            print(f"  Version: {soul_info['version']}")
            print(f"  Created: {soul_info['created_at']}")
            if soul_info['parent_hash']:
                print(f"  Parent: {soul_info['parent_hash'][:16]}...")
            print(f"  Report: {soul_info['report_file']}")
        else:
            print(f"❌ Soul {soul_hash} not found")
    
    async def promote_soul(self, soul_hash: str, environment: str = "production"):
        """Promuje Soul do środowiska produkcyjnego"""
        success = production_hash_manager.promote_to_production(soul_hash, environment)
        if success:
            print(f"✅ Soul promoted to {environment}")
        else:
            print(f"❌ Failed to promote soul")
    
    async def list_production(self, environment: str = "production"):
        """Lista souls w środowisku produkcyjnym"""
        souls = production_hash_manager.get_production_souls(environment)
        if souls:
            print(f"🏭 Production souls in '{environment}' ({len(souls)} total):")
            for hash_val, info in souls.items():
                print(f"  🧬 {hash_val[:16]}... - {info['alias']} (v{info['version']})")
        else:
            print(f"❌ No souls in {environment} environment")
    
    async def generate_manifest(self, environment: str = "production"):
        """Generuje manifest deploymentu"""
        manifest_path = production_hash_manager.generate_deployment_manifest(environment)
        print(f"📦 Manifest generated: {manifest_path}")
    
    async def validate_production(self, environment: str = "production"):
        """Waliduje hashe produkcyjne"""
        result = production_hash_manager.validate_production_hashes(environment)
        
        print(f"🔍 Production validation for '{environment}':")
        print(f"  ✅ Valid: {len(result['valid'])} souls")
        print(f"  ❌ Invalid: {len(result['invalid'])} souls")
        
        if result['invalid']:
            print("  Invalid hashes:")
            for hash_val in result['invalid']:
                print(f"    🚫 {hash_val[:16]}...")

async def main():
    parser = argparse.ArgumentParser(description="LuxOS Soul Management CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List souls')
    list_parser.add_argument('--alias', help='Filter by alias')
    
    # Show command  
    show_parser = subparsers.add_parser('show', help='Show soul details')
    show_parser.add_argument('hash', help='Soul hash')
    
    # Promote command
    promote_parser = subparsers.add_parser('promote', help='Promote soul to production')
    promote_parser.add_argument('hash', help='Soul hash')
    promote_parser.add_argument('--env', default='production', help='Target environment')
    
    # Production command
    prod_parser = subparsers.add_parser('production', help='List production souls')
    prod_parser.add_argument('--env', default='production', help='Environment')
    
    # Manifest command
    manifest_parser = subparsers.add_parser('manifest', help='Generate deployment manifest')
    manifest_parser.add_argument('--env', default='production', help='Environment')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate production hashes')
    validate_parser.add_argument('--env', default='production', help='Environment')
    
    args = parser.parse_args()
    cli = SoulManagerCLI()
    
    if args.command == 'list':
        await cli.list_souls(args.alias)
    elif args.command == 'show':
        await cli.show_soul(args.hash)
    elif args.command == 'promote':
        await cli.promote_soul(args.hash, args.env)
    elif args.command == 'production':
        await cli.list_production(args.env)
    elif args.command == 'manifest':
        await cli.generate_manifest(args.env)
    elif args.command == 'validate':
        await cli.validate_production(args.env)
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())
