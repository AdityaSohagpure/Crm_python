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

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlalchemy.future import select
import time

from backend_python.common.database import init_db, get_db_session, engine
from backend_python.common.models import Tenant, Deal
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
        deals_count = (await db.execute(text("SELECT count(*) FROM deals"))).scalar() or 0

        return {
            "status": "CONNECTED",
            "database_connected": True,
            "engine": dialect,
            "driver": driver,
            "latency_ms": latency_ms,
            "records": {
                "tenants": tenants_count,
                "users": users_count,
                "contacts": contacts_count,
                "deals": deals_count
            }
        }
    except Exception as e:
        return {
            "status": "DISCONNECTED",
            "database_connected": False,
            "error": str(e)
        }


# ==============================================================================
# DEALS API ENDPOINTS (PostgreSQL / SQLite Persistence)
# ==============================================================================

class CreateDealRequest(BaseModel):
    title: str
    company: str
    contactPerson: str
    contactEmail: Optional[str] = None
    contactPhone: Optional[str] = None
    value: Optional[int] = 0
    currency: Optional[str] = "INR"
    stage: Optional[str] = "New"
    score: Optional[int] = 50
    source: Optional[str] = "Website"
    priority: Optional[str] = "Medium"
    assignedTo: Optional[str] = "Ananya Sharma"
    expectedCloseDate: Optional[str] = None
    serviceCategory: Optional[str] = "Cloud Architecture & DevOps"
    notes: Optional[str] = None

class UpdateDealStageRequest(BaseModel):
    stage: str


@app.get("/api/v1/deals", tags=["Deals"])
async def list_deals(db: AsyncSession = Depends(get_db_session)):
    stmt = select(Deal).order_by(Deal.created_at.desc())
    res = await db.execute(stmt)
    deals = res.scalars().all()
    return {
        "success": True,
        "data": [
            {
                "id": d.id,
                "title": d.title,
                "company": d.company,
                "contactPerson": d.contact_person,
                "contactEmail": d.contact_email or "",
                "contactPhone": d.contact_phone or "",
                "value": d.value,
                "currency": d.currency,
                "stage": d.stage,
                "score": d.score,
                "source": d.source,
                "priority": d.priority,
                "assignedTo": d.assigned_to,
                "assignedAvatar": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150",
                "expectedCloseDate": d.expected_close_date or "",
                "daysInStage": 0,
                "serviceCategory": d.service_category,
                "notes": d.notes or "",
                "createdAt": d.created_at.strftime("%Y-%m-%d") if d.created_at else "",
                "updatedAt": d.updated_at.strftime("%Y-%m-%d") if d.updated_at else ""
            }
            for d in deals
        ]
    }


@app.post("/api/v1/deals", tags=["Deals"])
async def create_deal(req: CreateDealRequest, db: AsyncSession = Depends(get_db_session)):
    # Find or assign tenant
    t_res = await db.execute(select(Tenant))
    tenant = t_res.scalars().first()
    t_id = tenant.id if tenant else "default-tenant"

    deal = Deal(
        tenant_id=t_id,
        title=req.title,
        company=req.company,
        contact_person=req.contactPerson,
        contact_email=req.contactEmail,
        contact_phone=req.contactPhone,
        value=req.value or 0,
        currency=req.currency or "INR",
        stage=req.stage or "New",
        score=req.score or 50,
        source=req.source or "Website",
        priority=req.priority or "Medium",
        assigned_to=req.assignedTo or "Ananya Sharma",
        expected_close_date=req.expectedCloseDate,
        service_category=req.serviceCategory or "Cloud Architecture & DevOps",
        notes=req.notes
    )
    db.add(deal)
    await db.commit()
    await db.refresh(deal)

    return {
        "success": True,
        "data": {
            "id": deal.id,
            "title": deal.title,
            "company": deal.company,
            "contactPerson": deal.contact_person,
            "contactEmail": deal.contact_email or "",
            "contactPhone": deal.contact_phone or "",
            "value": deal.value,
            "currency": deal.currency,
            "stage": deal.stage,
            "score": deal.score,
            "source": deal.source,
            "priority": deal.priority,
            "assignedTo": deal.assigned_to,
            "assignedAvatar": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150",
            "expectedCloseDate": deal.expected_close_date or "",
            "daysInStage": 0,
            "serviceCategory": deal.service_category,
            "notes": deal.notes or "",
            "createdAt": deal.created_at.strftime("%Y-%m-%d") if deal.created_at else "",
            "updatedAt": deal.updated_at.strftime("%Y-%m-%d") if deal.updated_at else ""
        }
    }


@app.put("/api/v1/deals/{deal_id}/stage", tags=["Deals"])
async def update_deal_stage(deal_id: str, req: UpdateDealStageRequest, db: AsyncSession = Depends(get_db_session)):
    stmt = select(Deal).where(Deal.id == deal_id)
    res = await db.execute(stmt)
    deal = res.scalars().first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    deal.stage = req.stage
    await db.commit()
    return {"success": True, "data": {"id": deal.id, "stage": deal.stage}}


@app.delete("/api/v1/deals/{deal_id}", tags=["Deals"])
async def delete_deal(deal_id: str, db: AsyncSession = Depends(get_db_session)):
    stmt = select(Deal).where(Deal.id == deal_id)
    res = await db.execute(stmt)
    deal = res.scalars().first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    await db.delete(deal)
    await db.commit()
    return {"success": True, "message": "Deal deleted successfully"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend_python.main:app", host="0.0.0.0", port=port, reload=False)
