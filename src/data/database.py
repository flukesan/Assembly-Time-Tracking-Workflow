"""
Database Connection Manager
PostgreSQL connection pool and async operations
"""

import asyncio
from typing import Optional, List, Dict, Any
import asyncpg
from contextlib import asynccontextmanager
import logging
import os

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages PostgreSQL connection pool"""

    def __init__(
        self,
        host: str = None,
        port: int = None,
        database: str = None,
        user: str = None,
        password: str = None,
        min_size: int = 5,
        max_size: int = 20
    ):
        """
        Initialize database manager

        Args:
            host: PostgreSQL host
            port: PostgreSQL port
            database: Database name
            user: Username
            password: Password
            min_size: Minimum pool size
            max_size: Maximum pool size
        """
        # Load from environment if not provided
        self.host = host or os.getenv("POSTGRES_HOST", "localhost")
        self.port = port or int(os.getenv("POSTGRES_PORT", "5432"))
        self.database = database or os.getenv("POSTGRES_DB", "assembly_tracking")
        self.user = user or os.getenv("POSTGRES_USER", "assembly_user")
        self.password = password or os.getenv("POSTGRES_PASSWORD", "change_me_in_production")

        self.min_size = min_size
        self.max_size = max_size

        self.pool: Optional[asyncpg.Pool] = None
        self._lock = asyncio.Lock()

        logger.info(
            f"DatabaseManager initialized (host={self.host}, db={self.database})"
        )

    async def connect(self):
        """Create connection pool"""
        if self.pool is not None:
            logger.warning("Database pool already exists")
            return

        try:
            self.pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                min_size=self.min_size,
                max_size=self.max_size,
                command_timeout=60
            )

            logger.info(f"✅ Database pool created (min={self.min_size}, max={self.max_size})")

            # Test connection
            async with self.pool.acquire() as conn:
                version = await conn.fetchval("SELECT version()")
                logger.info(f"PostgreSQL version: {version[:50]}...")

        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise

    async def close(self):
        """Close connection pool"""
        if self.pool is None:
            return

        try:
            await self.pool.close()
            self.pool = None
            logger.info("✅ Database pool closed")

        except Exception as e:
            logger.error(f"Error closing database pool: {e}")

    @asynccontextmanager
    async def acquire(self):
        """
        Acquire connection from pool

        Usage:
            async with db_manager.acquire() as conn:
                await conn.execute("SELECT 1")
        """
        if self.pool is None:
            raise RuntimeError("Database pool not initialized. Call connect() first.")

        async with self.pool.acquire() as connection:
            yield connection

    async def execute(self, query: str, *args) -> str:
        """
        Execute a query (INSERT, UPDATE, DELETE)

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            Result status
        """
        async with self.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        """
        Fetch all rows

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            List of records
        """
        async with self.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """
        Fetch single row

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            Single record or None
        """
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args) -> Any:
        """
        Fetch single value

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            Single value
        """
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def executemany(self, query: str, args_list: List[tuple]) -> None:
        """
        Execute query multiple times (batch insert)

        Args:
            query: SQL query
            args_list: List of argument tuples
        """
        async with self.acquire() as conn:
            await conn.executemany(query, args_list)

    async def health_check(self) -> bool:
        """
        Check database health

        Returns:
            True if database is healthy
        """
        try:
            result = await self.fetchval("SELECT 1")
            return result == 1

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    async def get_table_count(self, table_name: str) -> int:
        """
        Get row count for a table

        Args:
            table_name: Table name

        Returns:
            Number of rows
        """
        query = f"SELECT COUNT(*) FROM {table_name}"
        return await self.fetchval(query)

    async def truncate_table(self, table_name: str):
        """
        Truncate a table (delete all rows)

        Args:
            table_name: Table name
        """
        query = f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE"
        await self.execute(query)
        logger.info(f"Truncated table: {table_name}")
