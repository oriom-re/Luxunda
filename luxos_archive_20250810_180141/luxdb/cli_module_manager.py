
"""
CLI do zarządzania systemem modułów LuxDB
"""

import asyncio
import click
from pathlib import Path
from .core.module_system import module_watcher
from .core.json_kernel_runner import json_kernel_runner
from .core.kernel_system import kernel_system

@click.group()
def cli():
    """LuxDB Module Management CLI"""
    pass

@cli.command()
@click.option('--paths', '-p', multiple=True, help='Ścieżki do skanowania')
async def scan(paths):
    """Skanuje i rejestruje moduły jako byty"""
    if paths:
        module_watcher.watch_paths = list(paths)
    
    print("🔍 Skanowanie modułów...")
    modules = await module_watcher.scan_and_register_all()
    
    print(f"✅ Zarejestrowano {len(modules)} modułów")
    
    # Wyświetl statystyki
    stats = module_watcher.get_module_stats()
    print("\n📊 Statystyki:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

@cli.command()
async def relationships():
    """Tworzy relacje między modułami"""
    print("🔗 Tworzenie relacji między modułami...")
    await module_watcher.create_module_relationships()
    print("✅ Relacje utworzone")

@cli.command()
def changelog():
    """Wyświetla historię zmian modułów"""
    changes = module_watcher.get_change_log()
    
    if not changes:
        print("📝 Brak zmian w historii")
        return
    
    print("📋 Historia zmian modułów:")
    print("-" * 80)
    
    for change in changes[-10:]:  # Ostatnie 10 zmian
        print(f"⏰ {change['timestamp']}")
        print(f"📁 {change['file_path']}")
        print(f"🔄 {change['action']} (hash: {change['new_hash'][:8]}...)")
        print(f"🆔 Being: {change['being_ulid'][:8]}...")
        print("-" * 40)

@cli.command()
@click.argument('config_path')
async def run_json(config_path):
    """Uruchamia system z konfiguracji JSON"""
    config_file = Path(config_path)
    
    if not config_file.exists():
        click.echo(f"❌ Plik konfiguracji nie istnieje: {config_path}")
        return
    
    print(f"🚀 Uruchamianie z konfiguracji: {config_path}")
    success = await json_kernel_runner.run_from_config(config_path)
    
    if success:
        print("✅ System uruchomiony pomyślnie")
    else:
        print("❌ Błąd uruchamiania systemu")

@cli.command()
@click.argument('scenario_name', default='default')
async def kernel(scenario_name):
    """Uruchamia system kernel ze scenariuszem"""
    print(f"🎬 Uruchamianie kernel ze scenariuszem: {scenario_name}")
    
    await kernel_system.initialize(scenario_name)
    status = await kernel_system.get_system_status()
    
    print("📊 Status systemu:")
    for key, value in status.items():
        if key != 'beings_list':
            print(f"  {key}: {value}")

@cli.command()
def stats():
    """Wyświetla statystyki modułów"""
    stats = module_watcher.get_module_stats()
    
    print("📊 Statystyki modułów:")
    print("=" * 40)
    
    for key, value in stats.items():
        print(f"{key}: {value}")

# Funkcja async wrapper dla click
def async_command(f):
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper

# Zastosuj wrapper do komend async
scan = async_command(scan)
relationships = async_command(relationships)
run_json = async_command(run_json)
kernel = async_command(kernel)

if __name__ == '__main__':
    cli()
