"""Client Supabase via PostgreSQL direct (pas REST API)"""

import asyncpg
from typing import Dict, List, Optional, Any
from app.config import settings
import logging
import json

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Client PostgreSQL direct pour Supabase"""
    
    def __init__(self):
        self.pool = None
        self.postgres_url = settings.postgres_connection_string
        logger.info(f"🔑 PostgreSQL: {self.postgres_url[:50]}...")
    
    async def connect(self):
        """Créer le pool de connexions"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                self.postgres_url,
                min_size=2,
                max_size=10
            )
            logger.info("✅ Pool PostgreSQL créé")
    
    async def select(
        self, 
        table: str, 
        columns: str = "*",
        filters: Optional[Dict[str, Any]] = None,
        order: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """SELECT query"""
        try:
            if not self.pool:
                await self.connect()
            
            # Construire la requête
            query = f"SELECT {columns} FROM public.{table}"
            params = []
            
            if filters:
                conditions = []
                param_num = 1
                for key, value in filters.items():
                    conditions.append(f"{key} = ${param_num}")
                    params.append(value)
                    param_num += 1
                query += " WHERE " + " AND ".join(conditions)
            
            if order:
                query += f" ORDER BY {order}"
            
            if limit:
                query += f" LIMIT {limit}"
            
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"❌ Erreur SELECT {table}: {e}")
            return []
    
    async def insert(
        self,
        table: str,
        data: Dict[str, Any]
    ) -> Optional[Dict]:
        """INSERT query"""
        try:
            if not self.pool:
                await self.connect()
            
            # Construire la requête
            columns = list(data.keys())
            placeholders = [f"${i+1}" for i in range(len(columns))]
            values = [data[col] for col in columns]
            
            query = f"""
                INSERT INTO public.{table} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                RETURNING *
            """
            
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, *values)
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"❌ Erreur INSERT {table}: {e}")
            return None
    
    async def upsert(
        self,
        table: str,
        data: Dict[str, Any],
        conflict_columns: List[str] = ['user_id', 'match_id']
    ) -> Optional[Dict]:
        """UPSERT query"""
        try:
            if not self.pool:
                await self.connect()
            
            # Construire la requête
            columns = list(data.keys())
            placeholders = [f"${i+1}" for i in range(len(columns))]
            values = [data[col] for col in columns]
            
            # Colonnes à update lors du conflit
            update_cols = [col for col in columns if col not in conflict_columns]
            update_set = ', '.join([f"{col} = EXCLUDED.{col}" for col in update_cols])
            
            query = f"""
                INSERT INTO public.{table} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                ON CONFLICT ({', '.join(conflict_columns)}) 
                DO UPDATE SET {update_set}
                RETURNING *
            """
            
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, *values)
                return dict(row) if row else None
                
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
        try:
            if not self.pool:
                await self.connect()
            
            # Construire SET clause
            set_clauses = []
            params = []
            param_num = 1
            
            for key, value in data.items():
                set_clauses.append(f"{key} = ${param_num}")
                params.append(value)
                param_num += 1
            
            # Construire WHERE clause
            where_clauses = []
            for key, value in filters.items():
                where_clauses.append(f"{key} = ${param_num}")
                params.append(value)
                param_num += 1
            
            query = f"""
                UPDATE public.{table}
                SET {', '.join(set_clauses)}
                WHERE {' AND '.join(where_clauses)}
            """
            
            async with self.pool.acquire() as conn:
                await conn.execute(query, *params)
                return True
                
        except Exception as e:
            logger.error(f"❌ Erreur UPDATE {table}: {e}")
            return False
    
    async def fetch(
        self,
        query: str,
        *params
    ) -> List[Dict]:
        """Exécuter une requête SQL brute"""
        try:
            if not self.pool:
                await self.connect()
            
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"❌ Erreur FETCH: {e}")
            return []
    
    async def close(self):
        """Fermer le pool"""
        if self.pool:
            await self.pool.close()
            logger.info("🛑 Pool PostgreSQL fermé")
