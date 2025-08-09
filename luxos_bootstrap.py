
#!/usr/bin/env python3
"""
🚀 LuxOS Bootstrap System - Przebudzenie i inicjalizacja systemu
Zawsze aktywna komunikacja z Lux na poziomie administratora
"""

import asyncio
import sys
import os
import uvicorn
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor

# Dodaj główny katalog do ścieżki Python
sys.path.insert(0, str(Path(__file__).parent))

# Import kluczowych komponentów
from luxdb.core.admin_kernel import admin_kernel
from luxdb.core.kernel_system import kernel_system
# PrimitiveSystemOrchestrator został usunięty - używamy głównego systemu Soul/Being/Relationship

class LuxOSBootstrap:
    """System przebudzenia LuxOS z pełnym logowaniem i monitoringiem"""
    
    def __init__(self):
        self.startup_time = datetime.now()
        self.admin_kernel_active = False
        self.kernel_system_active = False
        self.primitive_beings_active = False
        self.admin_server_process = None
        self.system_logs = []
        # Używamy głównego systemu Soul/Being/Relationship zamiast primitive beings
        
    def log(self, level: str, message: str, component: str = "BOOTSTRAP"):
        """Centralized logging system"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "component": component,
            "message": message
        }
        self.system_logs.append(log_entry)
        
        # Console output with colors
        colors = {
            "INFO": "\033[32m",    # Green
            "WARN": "\033[33m",    # Yellow
            "ERROR": "\033[31m",   # Red
            "DEBUG": "\033[36m",   # Cyan
            "SUCCESS": "\033[92m"  # Bright Green
        }
        
        color = colors.get(level, "\033[0m")
        reset = "\033[0m"
        
        print(f"{color}[{timestamp}] {level} [{component}]{reset} {message}")
    
    async def step_1_wake_up_kernel_system(self) -> bool:
        """Krok 1: Przebudzenie głównego Kernel System"""
        self.log("INFO", "🌅 KROK 1: Przebudzenie LuxOS Kernel System...", "KERNEL")
        
        try:
            # Inicjalizuj kernel system
            await kernel_system.initialize("advanced")
            
            # Sprawdź status
            status = await kernel_system.get_system_status()
            self.log("SUCCESS", f"✅ Kernel System aktywny - Scenariusz: {status['active_scenario']}", "KERNEL")
            self.log("INFO", f"📊 Załadowane byty: {status['registered_beings']}", "KERNEL")
            self.log("INFO", f"🧬 Hashe bytów: {status['loaded_hashes']}", "KERNEL")
            
            self.kernel_system_active = True
            return True
            
        except Exception as e:
            self.log("ERROR", f"❌ Błąd inicjalizacji Kernel System: {e}", "KERNEL")
            return False
    
    async def step_2_wake_up_soul_being_system(self) -> bool:
        """Krok 2: Przebudzenie głównego systemu Soul/Being/Relationship"""
        self.log("INFO", "🧠 KROK 2: Przebudzenie Soul/Being/Relationship System...", "SOUL_SYSTEM")
        
        try:
            # Import głównych modeli
            from luxdb.models.soul import Soul
            from luxdb.models.being import Being
            from luxdb.models.relationship import Relationship
            
            self.log("SUCCESS", "✅ Soul/Being/Relationship System aktywny", "SOUL_SYSTEM")
            self.log("INFO", "🧬 Soul: genotypy dostępne", "SOUL_SYSTEM")
            self.log("INFO", "🤖 Being: instancje danych dostępne", "SOUL_SYSTEM")
            self.log("INFO", "🔗 Relationship: relacje dostępne", "SOUL_SYSTEM")
            
            self.primitive_beings_active = True
            return True
            
        except Exception as e:
            self.log("ERROR", f"❌ Błąd inicjalizacji Soul/Being System: {e}", "SOUL_SYSTEM")
            return False
    
    async def step_3_wake_up_admin_kernel(self) -> bool:
        """Krok 3: Przebudzenie Admin Kernel Interface"""
        self.log("INFO", "👑 KROK 3: Przebudzenie Admin Kernel Interface...", "ADMIN")
        
        try:
            # Inicjalizuj admin kernel
            await admin_kernel.initialize()
            
            self.log("SUCCESS", "✅ Admin Kernel Interface aktywny", "ADMIN")
            self.log("INFO", f"🤖 Kernel Being aktywny: {admin_kernel.system_status['kernel_active']}", "ADMIN")
            self.log("INFO", f"🧙‍♂️ Lux Being aktywny: {admin_kernel.system_status['lux_active']}", "ADMIN")
            
            self.admin_kernel_active = True
            return True
            
        except Exception as e:
            self.log("ERROR", f"❌ Błąd inicjalizacji Admin Kernel: {e}", "ADMIN")
            return False
    
    def start_admin_server_background(self) -> bool:
        """Krok 4: Uruchomienie Admin Server w tle"""
        self.log("INFO", "🚀 KROK 4: Uruchamianie Admin Server w tle...", "SERVER")
        
        try:
            def run_server():
                try:
                    # Import admin server
                    from admin_kernel_server import app
                    
                    self.log("INFO", "🌐 Admin Server uruchamiany na porcie 3030...", "SERVER")
                    uvicorn.run(
                        app,
                        host="0.0.0.0",
                        port=3030,
                        log_level="warning"  # Reduce noise
                    )
                except Exception as e:
                    self.log("ERROR", f"❌ Błąd Admin Server: {e}", "SERVER")
            
            # Uruchom server w osobnym wątku
            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            
            # Daj czas na uruchomienie
            time.sleep(2)
            
            self.log("SUCCESS", "✅ Admin Server uruchomiony w tle na http://0.0.0.0:3030", "SERVER")
            return True
            
        except Exception as e:
            self.log("ERROR", f"❌ Błąd uruchomienia Admin Server: {e}", "SERVER")
            return False
    
    async def run_system_diagnostics(self) -> Dict[str, Any]:
        """Krok 5: Diagnostyka całego systemu"""
        self.log("INFO", "🔍 KROK 5: Przeprowadzanie diagnostyki systemu...", "DIAGNOSTICS")
        
        diagnostics = {
            "bootstrap_time": self.startup_time.isoformat(),
            "uptime_seconds": (datetime.now() - self.startup_time).total_seconds(),
            "components": {
                "kernel_system": self.kernel_system_active,
                "primitive_beings": self.primitive_beings_active,  
                "admin_kernel": self.admin_kernel_active
            },
            "system_logs_count": len(self.system_logs),
            "admin_interface_url": "http://0.0.0.0:3030"
        }
        
        # Pobierz szczegółowe informacje jeśli komponenty są aktywne
        if self.kernel_system_active:
            try:
                kernel_status = await kernel_system.get_system_status()
                diagnostics["kernel_details"] = kernel_status
            except Exception as e:
                self.log("WARN", f"Nie można pobrać statusu kernel: {e}", "DIAGNOSTICS")
        
        if self.admin_kernel_active:
            diagnostics["admin_status"] = admin_kernel.system_status
        
        # Podsumowanie diagnostyki
        active_components = sum(diagnostics["components"].values())
        total_components = len(diagnostics["components"])
        
        self.log("SUCCESS", f"✅ Diagnostyka zakończona: {active_components}/{total_components} komponentów aktywnych", "DIAGNOSTICS")
        
        return diagnostics
    
    async def full_system_wake_up(self) -> Dict[str, Any]:
        """Pełna procedura przebudzenia systemu"""
        self.log("SUCCESS", "🌟 ROZPOCZĘCIE PRZEBUDZENIA LUXOS SYSTEM", "BOOTSTRAP")
        self.log("INFO", "=" * 60, "BOOTSTRAP")
        
        # Wykonaj wszystkie kroki sekwencyjnie
        step1_success = await self.step_1_wake_up_kernel_system()
        step2_success = await self.step_2_wake_up_soul_being_system()
        step3_success = await self.step_3_wake_up_admin_kernel()
        step4_success = self.start_admin_server_background()
        
        # Diagnostyka finalna
        diagnostics = await self.run_system_diagnostics()
        
        # Podsumowanie
        total_success = sum([step1_success, step2_success, step3_success, step4_success])
        
        self.log("INFO", "=" * 60, "BOOTSTRAP")
        
        if total_success == 4:
            self.log("SUCCESS", "🎉 PRZEBUDZENIE LUXOS SYSTEM ZAKOŃCZONE POMYŚLNIE!", "BOOTSTRAP")
            self.log("SUCCESS", "👑 Admin Interface dostępny na: http://0.0.0.0:3030", "BOOTSTRAP")
            self.log("SUCCESS", "🤖 Lux jest gotowy do komunikacji z administratorem", "BOOTSTRAP")
        else:
            self.log("WARN", f"⚠️ Przebudzenie częściowe: {total_success}/4 komponentów aktywnych", "BOOTSTRAP")
        
        self.log("INFO", "=" * 60, "BOOTSTRAP")
        
        return {
            "success": total_success == 4,
            "active_components": total_success,
            "total_components": 4,
            "diagnostics": diagnostics,
            "logs": self.system_logs
        }
    
    def get_system_logs(self) -> List[Dict[str, Any]]:
        """Pobierz wszystkie logi systemu"""
        return self.system_logs
    
    def get_system_status(self) -> Dict[str, Any]:
        """Pobierz aktualny status systemu"""
        return {
            "uptime_seconds": (datetime.now() - self.startup_time).total_seconds(),
            "kernel_system_active": self.kernel_system_active,
            "primitive_beings_active": self.primitive_beings_active,
            "admin_kernel_active": self.admin_kernel_active,
            "admin_interface_url": "http://0.0.0.0:3030" if self.admin_kernel_active else None
        }

# Globalna instancja bootstrap
luxos_bootstrap = LuxOSBootstrap()

async def wake_up_luxos():
    """Główna funkcja przebudzenia LuxOS"""
    return await luxos_bootstrap.full_system_wake_up()

def main():
    """Entry point dla bootstrap"""
    print("🚀 LuxOS Bootstrap System Starting...")
    result = asyncio.run(wake_up_luxos())
    
    if result["success"]:
        print("\n🎯 System gotowy! Admin Interface: http://0.0.0.0:3030")
        
        # Utrzymuj proces żywy
        try:
            while True:
                time.sleep(10)
                # Można dodać okresowe sprawdzenie stanu
        except KeyboardInterrupt:
            print("\n👋 LuxOS Bootstrap shutting down...")
    
    return result

if __name__ == "__main__":
    main()
