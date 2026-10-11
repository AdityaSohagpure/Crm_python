import os
from typing import AsyncGenerator
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from backend_python.common.config import settings

def normalize_database_url(url: str) -> str:
    """Sanitize PostgreSQL connection strings from Neon/Supabase for asyncpg."""
    if "sqlite" in url:
        return url
    if url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]
    elif url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://"):]
    
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    query_params.pop("sslmode", None)
    query_params.pop("channel_binding", None)
    if "neon.tech" in url or "supabase" in url or "ssl" in parsed.query:
        query_params["ssl"] = ["require"]
        
    new_query = urlencode(query_params, doseq=True)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

raw_db_url = os.getenv("DATABASE_URL", settings.DATABASE_URL)
is_render = bool(os.getenv("RENDER") or os.getenv("RENDER_SERVICE_ID"))
is_local_db = "127.0.0.1" in raw_db_url or "localhost" in raw_db_url

if (os.getenv("USE_SQLITE", "false").lower() == "true" or "sqlite" in raw_db_url or (is_render and is_local_db)) and not ("neon.tech" in raw_db_url or "supabase" in raw_db_url):
    db_url = "sqlite+aiosqlite:///./cmr_crm.db"
    engine_kwargs = {"echo": False}
else:
    db_url = normalize_database_url(raw_db_url)
    engine_kwargs = {"echo": False, "future": True, "pool_size": 10, "max_overflow": 5, "connect_args": {"timeout": 10}}

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
