"""Client Supabase custom avec auth service_role forcée"""

import httpx
from typing import Dict, List, Optional, Any
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Client HTTP direct pour Supabase avec service_role"""
    
    def __init__(self):
        self.base_url = f"{settings.supabase_url}/rest/v1"
        self.headers = {
            "apikey": settings.supabase_service_key,
            "Authorization": f"Bearer {settings.supabase_service_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        self.client = httpx.AsyncClient(timeout=30.0)
        logger.info(f"🔑 Service key: {settings.supabase_service_key[:20]}...{settings.supabase_service_key[-10:]}")
    
    async def select(
        self, 
        table: str, 
        columns: str = "*",
        filters: Optional[Dict[str, Any]] = None,
        order: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """SELECT query"""
        url = f"{self.base_url}/{table}"
        params = {"select": columns}
        
        if filters:
            for key, value in filters.items():
                params[key] = f"eq.{value}"
        
        if order:
            params["order"] = order
        
        if limit:
            params["limit"] = str(limit)
        
        try:
            response = await self.client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ Erreur SELECT {table}: {e}")
            return []
    
    async def insert(
        self,
        table: str,
        data: Dict[str, Any]
    ) -> Optional[Dict]:
        """INSERT query"""
        url = f"{self.base_url}/{table}"
        
        try:
            response = await self.client.post(
                url, 
                headers=self.headers, 
                json=data
            )
            response.raise_for_status()
            result = response.json()
            return result[0] if result else None
        except Exception as e:
            logger.error(f"❌ Erreur INSERT {table}: {e}")
            return None
    
    async def upsert(
        self,
        table: str,
        data: Dict[str, Any]
    ) -> Optional[Dict]:
        """UPSERT query"""
        url = f"{self.base_url}/{table}"
        headers = {**self.headers, "Prefer": "resolution=merge-duplicates"}
        
        try:
            response = await self.client.post(
                url,
                headers=headers,
                json=data
            )
            response.raise_for_status()
            result = response.json()
            return result[0] if result else None
        except Exception as e:
            logger.error(f"❌ Erreur UPSERT {table}: {e}")
            return None
    
    async def update(
        self,
        table: str,
        data: Dict[str, Any],
        filters: Dict[str, Any]
    ) -> bool:
        """UPDATE query"""
        url = f"{self.base_url}/{table}"
        params = {}
        
        for key, value in filters.items():
            params[key] = f"eq.{value}"
        
        try:
            response = await self.client.patch(
                url,
                headers=self.headers,
                params=params,
                json=data
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"❌ Erreur UPDATE {table}: {e}")
            return False
    
    async def close(self):
        """Fermer le client"""
        await self.client.aclose()
