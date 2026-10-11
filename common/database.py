import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from backend_python.common.config import settings

db_url = settings.DATABASE_URL
is_render = bool(os.getenv("RENDER") or os.getenv("RENDER_SERVICE_ID"))
is_local_db = "127.0.0.1" in db_url or "localhost" in db_url

if os.getenv("USE_SQLITE", "false").lower() == "true" or "sqlite" in db_url or (is_render and is_local_db):
    db_url = "sqlite+aiosqlite:///./cmr_crm.db"
    engine_kwargs = {"echo": False}
else:
    engine_kwargs = {"echo": False, "future": True, "pool_size": 10, "max_overflow": 5, "connect_args": {"timeout": 5}}

engine = create_async_engine(db_url, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()
_db_initialized = False

async def init_db():
    global engine, AsyncSessionLocal, _db_initialized
    if _db_initialized:
        return
    _db_initialized = True

    try:
        async with engine.begin() as conn:
            from backend_python.common import models  # ensure models registered
            await conn.run_sync(Base.metadata.create_all)
        print(f"[DB Engine] Successfully initialized database tables on {engine.url.drivername}")
    except Exception as e:
        if "sqlite" not in str(engine.url):
            print(f"[DB Engine] Remote DB unreachable ({e}). Switching to SQLite engine...")
            fallback_url = "sqlite+aiosqlite:///./cmr_crm.db"
            engine = create_async_engine(fallback_url, echo=False)
            AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
        try:
            async with engine.begin() as conn:
                from backend_python.common import models
                await conn.run_sync(Base.metadata.create_all)
            print("[DB Engine] Successfully initialized SQLite fallback database tables!")
        except Exception:
            pass

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
