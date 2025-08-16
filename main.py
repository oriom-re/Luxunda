#!/usr/bin/env python3
"""
🌟 LuxOS Unified System - Jeden punkt wejścia dla całego systemu

Obsługuje:
- Simple Kernel (szybki start, podstawowe funkcje)
- Intelligent Kernel (zaawansowane funkcje, registry)
- Web Interface (interfejs użytkownika)
- Administration (zarządzanie systemem)
"""

import sys
import asyncio
import argparse
from typing import Dict, Any
from datetime import datetime
from pathlib import Path

# Core imports - tylko z luxdb
from luxdb.core.globals import Globals
from luxdb.core.postgre_db import Postgre_db
from luxdb.models.soul import Soul
from luxdb.models.being import Being
from luxdb.core import unified_kernel # Import zunifikowanego kernel

VERSION = "1.0.0"
SYSTEM_NAME = "LuxOS Unified"

class UnifiedSystemManager:
    """Unified manager for all LuxOS operations"""

    def __init__(self):
        self.kernel_type = None
        self.kernel_instance = None
        self.web_app = None
        self.status = "initializing"

    async def initialize_database(self):
        """Initialize PostgreSQL connection"""
        print("📊 Initializing PostgreSQL...")
        pool = await Postgre_db.get_db_pool()
        if not pool:
            raise Exception("Database connection failed")
        print("✅ Database connected")
        return True

    async def initialize_kernel(self, kernel_type: str = "simple"):
        """Initialize specified kernel type"""
        self.kernel_type = kernel_type

        if kernel_type == "simple":
            print("🧠 Initializing Simple Kernel...")
            from luxdb.core.simple_kernel import simple_kernel
            self.kernel_instance = await simple_kernel.initialize()

        elif kernel_type == "intelligent":
            print("🧠 Initializing Intelligent Kernel...")
            from luxdb.core.intelligent_kernel import intelligent_kernel
            self.kernel_instance = await intelligent_kernel.initialize()

        else:
            raise ValueError(f"Unknown kernel type: {kernel_type}")

        print(f"✅ {kernel_type.title()} Kernel initialized")
        return self.kernel_instance

    async def load_genotype_system(self):
        """Load genotype system if needed"""
        try:
            from luxdb.core import genotype_system
            print("🧬 Loading genotype system...")
            result = await genotype_system.initialize_system()

            if result["success"]:
                print(f"✅ Loaded {result['loaded_souls_count']} genotypes")
            else:
                print(f"⚠️ Genotype loading warning: {result.get('error')}")

        except Exception as e:
            print(f"⚠️ Genotype system not available: {e}")

    async def start_web_interface(self, port: int = 5000):
        """Start web interface"""
        print(f"🚀 Starting Web Interface on port {port}...")

        from luxdb.web_lux_interface import app
        import uvicorn

        config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

    async def run_administration_mode(self):
        """Run system administration"""
        print("🔧 LuxOS Administration Mode")

        # Initialize core systems
        await self.initialize_database()
        await self.initialize_kernel("intelligent")
        await self.load_genotype_system()

        # Status check
        souls = await Soul.get_all()
        beings = await Being.get_all()

        print(f"📊 System Status:")
        print(f"   Souls: {len(souls)}")
        print(f"   Beings: {len(beings)}")
        print(f"   Kernel: {self.kernel_instance.ulid[:8] if self.kernel_instance else 'None'}")

        return {
            "status": "operational",
            "souls_count": len(souls),
            "beings_count": len(beings),
            "kernel_type": self.kernel_type
        }

    async def run_full_system(self):
        """Run complete LuxOS system"""
        print(f"🌟 {SYSTEM_NAME} v{VERSION} - Full System")

        # Initialize all components
        await self.initialize_database()
        await self.initialize_kernel("intelligent")
        await self.load_genotype_system()

        # Start web interface
        await self.start_web_interface()

    async def run_minimal_system(self):
        """Run minimal system for development"""
        print(f"🌟 {SYSTEM_NAME} v{VERSION} - Minimal Mode")

        await self.initialize_database()
        await self.initialize_kernel("simple")

        # Quick test
        souls = await Soul.get_all()
        beings = await Being.get_all()

        print(f"✅ Minimal System OK: {len(souls)} souls, {len(beings)} beings")

        # Start simple web interface
        await self.start_web_interface()

# Global system manager
system_manager = UnifiedSystemManager()

async def main():
    """Main entry point with unified argument handling"""
    parser = argparse.ArgumentParser(description=f'{SYSTEM_NAME} v{VERSION}')

    # Primary modes
    parser.add_argument('--mode', choices=['web', 'admin', 'minimal', 'full'],
                       default='web', help='System operation mode')

    # Additional options
    parser.add_argument('--kernel', choices=['simple', 'intelligent'],
                       default='simple', help='Kernel type')
    parser.add_argument('--port', type=int, default=5000, help='Web interface port')
    parser.add_argument('--status', action='store_true', help='Show system status')
    parser.add_argument('--init-genotypes', action='store_true', help='Initialize genotypes')

    args = parser.parse_args()

    try:
        if args.status:
            result = await system_manager.run_administration_mode()
            print("✅ Status check completed")

        elif args.mode == 'admin':
            await system_manager.run_administration_mode()

        elif args.mode == 'minimal':
            await system_manager.run_minimal_system()

        elif args.mode == 'full':
            await system_manager.run_full_system()

        else:  # web mode (default)
            await system_manager.initialize_database()
            # Użycie zunifikowanego Kernel
            kernel_mode = "advanced" if args.kernel == "intelligent" else "simple"
            kernel_id = await unified_kernel.initialize(mode=kernel_mode)
            kernel = unified_kernel

            # 4. Initialize session manager for web interface
            from luxdb.core.session_data_manager import GlobalSessionRegistry
            session_manager = GlobalSessionRegistry()
            await session_manager.initialize()

            if args.init_genotypes:
                await system_manager.load_genotype_system()

            await system_manager.start_web_interface(args.port)

    except KeyboardInterrupt:
        print("\n👋 System interrupted")
    except Exception as e:
        print(f"❌ System error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())