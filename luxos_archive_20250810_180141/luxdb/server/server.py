
"""
LuxDB Server - Multi-tenant database server
"""

import asyncio
import json
import logging
from typing import Dict, Optional, Any, List
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager

from ..core.luxdb import LuxDB
from .namespace import NamespaceManager
from .schema_exporter import SchemaExporter
from .auth import AuthManager


logger = logging.getLogger(__name__)


class LuxDBServer:
    """
    LuxDB Server - Manages multiple isolated database namespaces
    """
    
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 5000,
        db_host: str = "localhost",
        db_port: int = 5432,
        db_user: str = None,
        db_password: str = None,
        db_name: str = "luxdb",
        enable_auth: bool = False
    ):
        self.host = host
        self.port = port
        self.db_config = {
            "host": db_host,
            "port": db_port,
            "user": db_user,
            "password": db_password,
            "database": db_name
        }
        self.enable_auth = enable_auth
        
        # Managers
        self.namespace_manager = NamespaceManager(self.db_config)
        self.schema_exporter = SchemaExporter()
        self.auth_manager = AuthManager() if enable_auth else None
        
        # FastAPI app
        self.app = self._create_app()
        
    def _create_app(self) -> FastAPI:
        """Create FastAPI application with all routes"""
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            await self.namespace_manager.initialize()
            logger.info(f"🚀 LuxDB Server started on {self.host}:{self.port}")
            yield
            # Shutdown
            await self.namespace_manager.close()
            logger.info("🔄 LuxDB Server stopped")
        
        app = FastAPI(
            title="LuxDB Server",
            description="Multi-tenant genetic database server",
            version="1.0.0",
            lifespan=lifespan
        )
        
        # CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Routes
        self._add_routes(app)
        
        return app
    
    def _add_routes(self, app: FastAPI):
        """Add all API routes"""
        
        @app.get("/")
        async def root():
            return {
                "service": "LuxDB Server",
                "version": "1.0.0",
                "status": "running",
                "namespaces": await self.namespace_manager.list_namespaces()
            }
        
        @app.post("/namespaces/{namespace_id}")
        async def create_namespace(namespace_id: str, config: Dict[str, Any] = None):
            """Create new isolated namespace"""
            try:
                result = await self.namespace_manager.create_namespace(namespace_id, config or {})
                return {"success": True, "namespace": namespace_id, "result": result}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @app.get("/namespaces")
        async def list_namespaces():
            """List all available namespaces"""
            return await self.namespace_manager.list_namespaces()
        
        @app.get("/namespaces/{namespace_id}")
        async def get_namespace_info(namespace_id: str):
            """Get namespace information"""
            try:
                info = await self.namespace_manager.get_namespace_info(namespace_id)
                return info
            except Exception as e:
                raise HTTPException(status_code=404, detail=str(e))
        
        @app.delete("/namespaces/{namespace_id}")
        async def delete_namespace(namespace_id: str):
            """Delete namespace"""
            try:
                result = await self.namespace_manager.delete_namespace(namespace_id)
                return {"success": True, "result": result}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        # Soul operations
        @app.get("/namespaces/{namespace_id}/souls")
        async def list_souls(namespace_id: str):
            """List all souls in namespace"""
            try:
                db = await self.namespace_manager.get_database(namespace_id)
                from ..models.soul import Soul
                souls = await Soul.load_all()
                return [soul.to_dict() for soul in souls]
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @app.post("/namespaces/{namespace_id}/souls")
        async def create_soul(namespace_id: str, soul_data: Dict[str, Any]):
            """Create new soul in namespace"""
            try:
                db = await self.namespace_manager.get_database(namespace_id)
                from ..models.soul import Soul
                soul = await Soul.create(
                    soul_data["genotype"], 
                    soul_data.get("alias")
                )
                return {"success": True, "soul": soul.to_dict()}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        # Being operations
        @app.get("/namespaces/{namespace_id}/beings")
        async def list_beings(namespace_id: str):
            """List all beings in namespace"""
            try:
                db = await self.namespace_manager.get_database(namespace_id)
                from ..models.being import Being
                beings = await Being.load_all()
                return [being.to_dict() for being in beings]
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @app.post("/namespaces/{namespace_id}/beings")
        async def create_being(namespace_id: str, being_data: Dict[str, Any]):
            """Create new being in namespace"""
            try:
                db = await self.namespace_manager.get_database(namespace_id)
                from ..models.soul import Soul
                from ..models.being import Being
                
                soul = await Soul.load_by_hash(being_data["soul_hash"])
                if not soul:
                    raise HTTPException(status_code=404, detail="Soul not found")
                
                being = await Being.create(
                    soul,
                    being_data["data"],
                    being_data.get("alias")
                )
                return {"success": True, "being": being.to_dict()}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        # Schema export/import
        @app.get("/namespaces/{namespace_id}/schema/export")
        async def export_schema(namespace_id: str):
            """Export namespace schema to JSON"""
            try:
                db = await self.namespace_manager.get_database(namespace_id)
                schema = await self.schema_exporter.export_namespace_schema(namespace_id, db)
                return schema
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @app.post("/namespaces/{namespace_id}/schema/import")
        async def import_schema(namespace_id: str, schema_data: Dict[str, Any]):
            """Import schema to namespace"""
            try:
                db = await self.namespace_manager.get_database(namespace_id)
                result = await self.schema_exporter.import_namespace_schema(namespace_id, db, schema_data)
                return {"success": True, "result": result}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        # Health check
        @app.get("/health")
        async def health_check():
            """Server health check"""
            try:
                health_data = {}
                for namespace_id in await self.namespace_manager.list_namespaces():
                    db = await self.namespace_manager.get_database(namespace_id)
                    health_data[namespace_id] = await db.health_check()
                
                return {
                    "status": "healthy",
                    "namespaces": health_data
                }
            except Exception as e:
                return {"status": "error", "error": str(e)}
    
    async def start(self):
        """Start the server"""
        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
    
    def run(self):
        """Run the server (blocking)"""
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )


# CLI function for starting server
async def start_server(
    host: str = "0.0.0.0",
    port: int = 5000,
    db_host: str = "localhost",
    db_port: int = 5432,
    db_user: str = None,
    db_password: str = None,
    db_name: str = "luxdb"
):
    """Start LuxDB server from command line"""
    server = LuxDBServer(
        host=host,
        port=port,
        db_host=db_host,
        db_port=db_port,
        db_user=db_user,
        db_password=db_password,
        db_name=db_name
    )
    await server.start()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = 5000
    
    server = LuxDBServer(port=port)
    server.run()
