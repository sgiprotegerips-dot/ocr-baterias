"""Configuración de conexión y sesiones de base de datos relacional (PostgreSQL / SQLite)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Obtener URL de base de datos desde entorno
# En Docker/Producción: postgresql+asyncpg://bateria_admin:ClaveSeguraSST2026!@db:5432/bateria_sst
# Fallback local de desarrollo: sqlite en ./data/bateria_sst.db
DEFAULT_SQLITE_ASYNC = f"sqlite+aiosqlite:///{DATA_DIR / 'bateria_sst.db'}"
DEFAULT_SQLITE_SYNC = f"sqlite:///{DATA_DIR / 'bateria_sst.db'}"

raw_url = os.environ.get("DATABASE_URL")
if raw_url:
    ASYNC_DATABASE_URL = raw_url
    if "+asyncpg" in raw_url:
        SYNC_DATABASE_URL = raw_url.replace("+asyncpg", "+psycopg2")
    elif "+aiosqlite" in raw_url:
        SYNC_DATABASE_URL = raw_url.replace("+aiosqlite", "")
    elif raw_url.startswith("postgresql://"):
        SYNC_DATABASE_URL = raw_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    else:
        SYNC_DATABASE_URL = raw_url
else:
    # Intentar verificar si postgres local está accesible, de lo contrario SQLite
    ASYNC_DATABASE_URL = os.environ.get("DATABASE_URL_ASYNC", DEFAULT_SQLITE_ASYNC)
    SYNC_DATABASE_URL = os.environ.get("DATABASE_URL_SYNC", DEFAULT_SQLITE_SYNC)

if SYNC_DATABASE_URL.startswith("postgresql://"):
    SYNC_DATABASE_URL = SYNC_DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

# Base declarativa de modelos
Base = declarative_base()

# Motores Asíncronos
engine_args = {"echo": False, "future": True}
if "sqlite" in ASYNC_DATABASE_URL:
    engine_args["connect_args"] = {"check_same_thread": False}

async_engine = create_async_engine(ASYNC_DATABASE_URL, **engine_args)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Motores Síncronos (para inicialización y tareas offline)
sync_engine_args = {"echo": False, "future": True}
if "sqlite" in SYNC_DATABASE_URL:
    sync_engine_args["connect_args"] = {"check_same_thread": False}

sync_engine = create_engine(SYNC_DATABASE_URL, **sync_engine_args)
SyncSessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Inyector de dependencia para FastAPI (Sesión asíncrona)."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_db() -> Generator:
    """Inyector o manejador de sesión síncrona."""
    session = SyncSessionLocal()
    try:
        yield session
    finally:
        session.close()
