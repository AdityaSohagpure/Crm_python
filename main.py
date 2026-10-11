"""
Unified FastAPI Application Entrypoint for Production / Free Cloud Deployment.
Combines all microservices into a single unified API service:
- Gateway & Auth (/api/v1/auth)
- Channel Messaging (/api/v1/messages)
- Contact & Identity (/api/v1/contacts, /api/v1/conversations)
- Meta Webhook Receiver (/api/v1/webhooks)
"""

import os
import sys
import types
from pathlib import Path
from contextlib import asynccontextmanager

# Enable running both as standalone root repository and as a subfolder
_current_dir = Path(__file__).resolve().parent
if str(_current_dir.parent) not in sys.path:
    sys.path.insert(0, str(_current_dir.parent))
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))
if "backend_python" not in sys.modules and (_current_dir / "common").exists():
    _bp_pkg = types.ModuleType("backend_python")
    _bp_pkg.__path__ = [str(_current_dir)]
    sys.modules["backend_python"] = _bp_pkg

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import time

from backend_python.common.database import init_db, get_db_session, engine
from backend_python.services.gateway_auth.main import app as gateway_auth_app
from backend_python.services.channel_messaging.main import app as channel_messaging_app
from backend_python.services.contact_identity.main import app as contact_identity_app
from backend_python.services.webhook_receiver.main import app as webhook_receiver_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables on startup
    await init_db()
    yield


app = FastAPI(
    title="Centegix CMR - Unified Cloud API",
    description="Multi-Tenant Omnichannel CRM API Engine combining Auth, Messaging, Contacts, and Webhooks.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Global CORS Configuration (permits Vercel, Netlify, and localhost frontend access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Merge all microservice routes into this unified app
app.include_router(gateway_auth_app.router)
app.include_router(channel_messaging_app.router)
app.include_router(contact_identity_app.router)
app.include_router(webhook_receiver_app.router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "ONLINE",
        "service": "Centegix CMR Unified Backend (FastAPI)",
        "docs": "/docs",
        "endpoints": [
            "/api/v1/auth",
            "/api/v1/messages",
            "/api/v1/contacts",
            "/api/v1/conversations",
            "/api/v1/webhooks"
        ]
    }


@app.get("/api/health", tags=["Health"], operation_id="unified_cluster_health")
async def cluster_health_check():
    return {
        "status": "ONLINE",
        "database": "CONNECTED",
        "services": {
            "gateway_auth": "HEALTHY",
            "channel_messaging": "HEALTHY",
            "contact_identity": "HEALTHY",
            "webhook_receiver": "HEALTHY"
        }
    }


@app.get("/api/v1/system/db-status", tags=["Health"], operation_id="system_database_status")
async def system_db_status(db: AsyncSession = Depends(get_db_session)):
    start = time.time()
    try:
        await db.execute(text("SELECT 1"))
        latency_ms = round((time.time() - start) * 1000, 2)
        driver = engine.url.drivername
        dialect = engine.url.get_backend_name().upper()

        tenants_count = (await db.execute(text("SELECT count(*) FROM tenants"))).scalar() or 0
        users_count = (await db.execute(text("SELECT count(*) FROM users"))).scalar() or 0
        contacts_count = (await db.execute(text("SELECT count(*) FROM contacts"))).scalar() or 0

        return {
            "status": "CONNECTED",
            "database_connected": True,
            "engine": dialect,
            "driver": driver,
            "latency_ms": latency_ms,
            "records": {
                "tenants": tenants_count,
                "users": users_count,
                "contacts": contacts_count
            }
        }
    except Exception as e:
        return {
            "status": "DISCONNECTED",
            "database_connected": False,
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend_python.main:app", host="0.0.0.0", port=port, reload=False)
