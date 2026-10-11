import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from backend_python.common.config import settings

db_url = settings.DATABASE_URL
if os.getenv("USE_SQLITE", "false").lower() == "true" or "sqlite" in db_url:
    db_url = "sqlite+aiosqlite:///./cmr_crm.db"
    engine_kwargs = {"echo": False}
else:
    engine_kwargs = {"echo": False, "future": True, "pool_size": 20, "max_overflow": 10}

engine = create_async_engine(db_url, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def init_db():
    global engine, AsyncSessionLocal
    try:
        async with engine.begin() as conn:
            from backend_python.common import models  # ensure models registered
            await conn.run_sync(Base.metadata.create_all)
        print(f"[DB Engine] Successfully initialized database tables on {engine.url.drivername}")
    except Exception as e:
        if "sqlite" not in str(engine.url):
            print(f"[DB Engine] PostgreSQL unreachable ({e}). Switching to SQLite local engine...")
            fallback_url = "sqlite+aiosqlite:///./cmr_crm.db"
            engine = create_async_engine(fallback_url, echo=False)
            AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
        try:
            async with engine.begin() as conn:
                from backend_python.common import models
                await conn.run_sync(Base.metadata.create_all)
            print("[DB Engine] Successfully initialized SQLite fallback database tables!")
        except Exception as sqlite_err:
            # Table already created by parallel microservice process
            pass

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
