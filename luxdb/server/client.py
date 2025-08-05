
"""
LuxDB Client - Connects to LuxDB Server instances
"""

import aiohttp
import json
from typing import Dict, List, Optional, Any
from ..models.soul import Soul
from ..models.being import Being


class LuxDBClient:
    """
    Client for connecting to remote LuxDB server instances
    """
    
    def __init__(
        self, 
        server_url: str = "http://localhost:5000",
        namespace_id: str = "default",
        auth_token: Optional[str] = None
    ):
        self.server_url = server_url.rstrip('/')
        self.namespace_id = namespace_id
        self.auth_token = auth_token
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def connect(self):
        """Create HTTP session"""
        headers = {}
        if self.auth_token:
            headers['Authorization'] = f"Bearer {self.auth_token}"
        
        self.session = aiohttp.ClientSession(
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
    
    def _get_url(self, endpoint: str) -> str:
        """Build full URL for endpoint"""
        endpoint = endpoint.lstrip('/')
        return f"{self.server_url}/{endpoint}"
    
    def _get_namespace_url(self, endpoint: str) -> str:
        """Build namespaced URL"""
        endpoint = endpoint.lstrip('/')
        return self._get_url(f"namespaces/{self.namespace_id}/{endpoint}")
    
    async def _request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request"""
        if not self.session:
            await self.connect()
        
        async with self.session.request(method, url, **kwargs) as response:
            response.raise_for_status()
            return await response.json()
    
    # Server operations
    async def get_server_info(self) -> Dict[str, Any]:
        """Get server information"""
        return await self._request('GET', self._get_url('/'))
    
    async def health_check(self) -> Dict[str, Any]:
        """Check server health"""
        return await self._request('GET', self._get_url('/health'))
    
    # Namespace operations
    async def create_namespace(self, namespace_id: str = None, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create new namespace"""
        ns_id = namespace_id or self.namespace_id
        url = self._get_url(f'/namespaces/{ns_id}')
        return await self._request('POST', url, json=config or {})
    
    async def list_namespaces(self) -> List[str]:
        """List available namespaces"""
        return await self._request('GET', self._get_url('/namespaces'))
    
    async def get_namespace_info(self) -> Dict[str, Any]:
        """Get current namespace information"""
        url = self._get_url(f'/namespaces/{self.namespace_id}')
        return await self._request('GET', url)
    
    async def delete_namespace(self, namespace_id: str = None) -> Dict[str, Any]:
        """Delete namespace"""
        ns_id = namespace_id or self.namespace_id
        url = self._get_url(f'/namespaces/{ns_id}')
        return await self._request('DELETE', url)
    
    # Soul operations
    async def create_soul(self, genotype: Dict[str, Any], alias: str = None) -> Dict[str, Any]:
        """Create soul in current namespace"""
        url = self._get_namespace_url('/souls')
        data = {"genotype": genotype, "alias": alias}
        return await self._request('POST', url, json=data)
    
    async def list_souls(self) -> List[Dict[str, Any]]:
        """List all souls in current namespace"""
        url = self._get_namespace_url('/souls')
        return await self._request('GET', url)
    
    # Being operations
    async def create_being(self, soul_hash: str, data: Dict[str, Any], alias: str = None) -> Dict[str, Any]:
        """Create being in current namespace"""
        url = self._get_namespace_url('/beings')
        payload = {"soul_hash": soul_hash, "data": data, "alias": alias}
        return await self._request('POST', url, json=payload)
    
    async def list_beings(self) -> List[Dict[str, Any]]:
        """List all beings in current namespace"""
        url = self._get_namespace_url('/beings')
        return await self._request('GET', url)
    
    # Schema operations
    async def export_schema(self) -> Dict[str, Any]:
        """Export current namespace schema"""
        url = self._get_namespace_url('/schema/export')
        return await self._request('GET', url)
    
    async def import_schema(self, schema_data: Dict[str, Any]) -> Dict[str, Any]:
        """Import schema to current namespace"""
        url = self._get_namespace_url('/schema/import')
        return await self._request('POST', url, json=schema_data)
    
    async def save_schema_to_file(self, filename: str):
        """Export schema and save to file"""
        schema = await self.export_schema()
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
    
    async def load_schema_from_file(self, filename: str) -> Dict[str, Any]:
        """Load schema from file and import to namespace"""
        with open(filename, 'r', encoding='utf-8') as f:
            schema_data = json.load(f)
        return await self.import_schema(schema_data)
    
    # Convenience methods
    async def setup_namespace(self, namespace_id: str = None) -> Dict[str, Any]:
        """Setup namespace if it doesn't exist"""
        ns_id = namespace_id or self.namespace_id
        try:
            return await self.get_namespace_info()
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                # Namespace doesn't exist, create it
                return await self.create_namespace(ns_id)
            raise


# Factory function for quick client creation
def connect_to_luxdb(
    server_url: str = "http://localhost:5000",
    namespace_id: str = "default",
    auth_token: Optional[str] = None
) -> LuxDBClient:
    """
    Create LuxDB client connection
    
    Example:
        ```python
        client = connect_to_luxdb("http://localhost:5000", "my_project")
        async with client:
            souls = await client.list_souls()
        ```
    """
    return LuxDBClient(server_url, namespace_id, auth_token)
