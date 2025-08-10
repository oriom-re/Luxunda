
#!/usr/bin/env python3
"""
LuxOS Scenario Manager - CLI do zarządzania scenariuszami
"""

import asyncio
import argparse
import json
from pathlib import Path
from luxdb.core.kernel_system import KernelSystem, ScenarioLoader

async def list_scenarios():
    """Lista dostępnych scenariuszy"""
    scenarios_path = Path("scenarios")
    if not scenarios_path.exists():
        print("📂 Brak katalogu scenarios")
        return
    
    scenarios = list(scenarios_path.glob("*.scenario"))
    
    print("📋 Dostępne scenariusze:")
    for scenario_file in scenarios:
        with open(scenario_file, 'r') as f:
            data = json.load(f)
        
        print(f"  🎬 {data['name']}")
        print(f"     Bytów: {len(data['beings'])}")
        print(f"     Utworzony: {data['created_at'][:19]}")
        print()

async def show_scenario(scenario_name: str):
    """Pokazuje szczegóły scenariusza"""
    loader = ScenarioLoader()
    scenario_file = Path(f"scenarios/{scenario_name}.scenario")
    
    if not scenario_file.exists():
        print(f"❌ Scenariusz {scenario_name} nie istnieje")
        return
    
    with open(scenario_file, 'r') as f:
        data = json.load(f)
    
    print(f"🎬 Scenariusz: {data['name']}")
    print(f"📅 Utworzony: {data['created_at']}")
    print(f"🧬 Byty ({len(data['beings'])}):")
    
    for being in sorted(data['beings'], key=lambda x: x['load_order']):
        print(f"  {being['load_order']:2d}. {being['hash'][:12]}...")
        if being['dependencies']:
            print(f"      Zależy od: {', '.join([dep[:8] + '...' for dep in being['dependencies']])}")

async def run_scenario(scenario_name: str):
    """Uruchamia scenariusz"""
    kernel = KernelSystem()
    
    try:
        await kernel.initialize(scenario_name)
        status = await kernel.get_system_status()
        
        print(f"✅ Uruchomiono scenariusz: {scenario_name}")
        print(f"📊 Załadowano {status['registered_beings']} bytów")
        
        # Pokazuj status przez 10 sekund
        for i in range(10):
            await asyncio.sleep(1)
            print(f"⏱️ System działa... {10-i}s")
        
    except Exception as e:
        print(f"❌ Błąd uruchamiania: {e}")

async def create_being(scenario_name: str, being_data: dict):
    """Tworzy nowy byt i dodaje do scenariusza"""
    loader = ScenarioLoader()
    
    # Utwórz hash dla bytu
    being_hash = loader.create_being_hash(being_data)
    
    # Zapisz byt
    being_file = Path(f"scenarios/{being_hash}.json")
    with open(being_file, 'w') as f:
        json.dump(being_data, f, indent=2)
    
    print(f"🆕 Utworzono nowy byt: {being_hash[:12]}...")
    print(f"💾 Zapisano w: {being_file}")
    
    return being_hash

def main():
    """CLI główne"""
    parser = argparse.ArgumentParser(description="LuxOS Scenario Manager")
    subparsers = parser.add_subparsers(dest='command', help='Dostępne komendy')
    
    # Lista scenariuszy
    subparsers.add_parser('list', help='Lista scenariuszy')
    
    # Pokazuj scenariusz  
    show_parser = subparsers.add_parser('show', help='Pokaż szczegóły scenariusza')
    show_parser.add_argument('name', help='Nazwa scenariusza')
    
    # Uruchom scenariusz
    run_parser = subparsers.add_parser('run', help='Uruchom scenariusz')
    run_parser.add_argument('name', help='Nazwa scenariusza')
    
    # Utwórz byt
    create_parser = subparsers.add_parser('create-being', help='Utwórz nowy byt')
    create_parser.add_argument('--alias', required=True, help='Alias bytu')
    create_parser.add_argument('--type', default='generic', help='Typ bytu')
    create_parser.add_argument('--priority', type=int, default=50, help='Priorytet')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        asyncio.run(list_scenarios())
    elif args.command == 'show':
        asyncio.run(show_scenario(args.name))
    elif args.command == 'run':
        asyncio.run(run_scenario(args.name))
    elif args.command == 'create-being':
        being_data = {
            "alias": args.alias,
            "soul_alias": f"{args.alias}_soul",
            "genotype": {
                "genesis": {
                    "name": args.alias,
                    "type": args.type,
                    "doc": f"Byt {args.alias} typu {args.type}"
                }
            },
            "attributes": {
                "priority": args.priority,
                "created_by": "scenario_manager"
            },
            "load_order": args.priority
        }
        asyncio.run(create_being(args.alias, being_data))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
