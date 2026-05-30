"""Database setup - SQLite (for query logs only, Chroma handles vector storage)."""
import os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

DB_DIR = Path(__file__).resolve().parent.parent / "data"
os.makedirs(str(DB_DIR), exist_ok=True)
DB_PATH = str(DB_DIR / "rag_logs.db")
ASYNC_DB_URL = f"sqlite+aiosqlite:///{DB_PATH}"

engine = create_async_engine(ASYNC_DB_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def close_db():
    await engine.dispose()
