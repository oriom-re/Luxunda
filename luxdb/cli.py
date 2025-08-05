
"""
LuxDB Command Line Interface
"""

import asyncio
import argparse
import sys
import json
from typing import Optional

from .server.server import LuxDBServer
from .server.client import LuxDBClient


async def start_server_command(args):
    """Start LuxDB server"""
    print(f"🚀 Starting LuxDB Server on {args.host}:{args.port}")
    
    server = LuxDBServer(
        host=args.host,
        port=args.port,
        db_host=args.db_host,
        db_port=args.db_port,
        db_user=args.db_user,
        db_password=args.db_password,
        db_name=args.db_name,
        enable_auth=args.enable_auth
    )
    
    await server.start()


async def client_command(args):
    """Client operations"""
    client = LuxDBClient(
        server_url=args.server_url,
        namespace_id=args.namespace,
        auth_token=args.token
    )
    
    async with client:
        if args.client_action == "info":
            info = await client.get_server_info()
            print(json.dumps(info, indent=2))
        
        elif args.client_action == "namespaces":
            namespaces = await client.list_namespaces()
            print("Available namespaces:")
            for ns in namespaces:
                print(f"  - {ns}")
        
        elif args.client_action == "create-namespace":
            result = await client.create_namespace(args.namespace)
            print(f"✅ Namespace '{args.namespace}' created")
            print(json.dumps(result, indent=2))
        
        elif args.client_action == "export-schema":
            schema = await client.export_schema()
            filename = args.output or f"{args.namespace}_schema.json"
            await client.save_schema_to_file(filename)
            print(f"✅ Schema exported to {filename}")
        
        elif args.client_action == "import-schema":
            if not args.input:
                print("❌ Input file required for import-schema")
                return
            result = await client.load_schema_from_file(args.input)
            print(f"✅ Schema imported from {args.input}")
            print(json.dumps(result, indent=2))
        
        elif args.client_action == "souls":
            souls = await client.list_souls()
            print(f"Souls in namespace '{args.namespace}':")
            for soul in souls:
                print(f"  - {soul.get('alias', 'unnamed')}: {soul.get('soul_hash', '')[:16]}...")
        
        elif args.client_action == "beings":
            beings = await client.list_beings()
            print(f"Beings in namespace '{args.namespace}':")
            for being in beings:
                print(f"  - {being.get('alias', 'unnamed')}: {being.get('ulid', '')}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="LuxDB - Genetic Database System")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Server command
    server_parser = subparsers.add_parser("server", help="Start LuxDB server")
    server_parser.add_argument("--host", default="0.0.0.0", help="Server host")
    server_parser.add_argument("--port", type=int, default=5000, help="Server port")
    server_parser.add_argument("--db-host", default="localhost", help="Database host")
    server_parser.add_argument("--db-port", type=int, default=5432, help="Database port")
    server_parser.add_argument("--db-user", help="Database user")
    server_parser.add_argument("--db-password", help="Database password")
    server_parser.add_argument("--db-name", default="luxdb", help="Database name")
    server_parser.add_argument("--enable-auth", action="store_true", help="Enable authentication")
    
    # Client command
    client_parser = subparsers.add_parser("client", help="LuxDB client operations")
    client_parser.add_argument("--server-url", default="http://localhost:5000", help="Server URL")
    client_parser.add_argument("--namespace", default="default", help="Namespace to use")
    client_parser.add_argument("--token", help="Authentication token")
    client_parser.add_argument("client_action", choices=[
        "info", "namespaces", "create-namespace", "export-schema", 
        "import-schema", "souls", "beings"
    ], help="Client action to perform")
    client_parser.add_argument("--output", help="Output file for export operations")
    client_parser.add_argument("--input", help="Input file for import operations")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "server":
            asyncio.run(start_server_command(args))
        elif args.command == "client":
            asyncio.run(client_command(args))
    except KeyboardInterrupt:
        print("\n🔄 Operation cancelled")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
