from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend_python.common.database import get_db_session, init_db
from backend_python.common.models import Tenant, User
from backend_python.common.security import create_jwt_token, verify_jwt_token

app = FastAPI(
    title="Gateway & Auth Microservice",
    description="Multi-Tenant Auth, Tenant Registration, and JWT Security Provider",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    await init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RegisterTenantRequest(BaseModel):
    companyName: str
    companySlug: str
    adminName: str
    adminEmail: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@app.get("/api/health")
async def health_check():
    return {
        "status": "ONLINE",
        "service": "Python Microservice Gateway & Auth Engine",
        "framework": "FastAPI + AsyncPG PostgreSQL"
    }

@app.post("/api/v1/auth/register-tenant", status_code=status.HTTP_201_CREATED)
async def register_tenant(req: RegisterTenantRequest, db: AsyncSession = Depends(get_db_session)):
    slug_lower = req.companySlug.lower()
    
    # Check existing slug
    result = await db.execute(select(Tenant).where(Tenant.slug == slug_lower))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tenant slug is already taken."
        )

    # Create Tenant
    tenant = Tenant(
        name=req.companyName,
        slug=slug_lower,
        plan="STARTER",
        status="ACTIVE"
    )
    db.add(tenant)
    await db.flush()

    # Create Tenant Admin User
    user = User(
        tenant_id=tenant.id,
        name=req.adminName,
        email=req.adminEmail.lower(),
        password_hash=req.password, # In production use passlib bcrypt/argon2
        role="TENANT_ADMIN",
        is_active=True
    )
    db.add(user)
    await db.commit()

    # Issue JWT
    token = create_jwt_token({
        "userId": user.id,
        "tenantId": tenant.id,
        "email": user.email,
        "role": user.role
    })

    return {
        "success": True,
        "data": {
            "token": token,
            "tenant": {"id": tenant.id, "name": tenant.name, "slug": tenant.slug, "plan": tenant.plan},
            "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role}
        }
    }

@app.post("/api/v1/auth/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(User).where(User.email == req.email.lower()))
    user = result.scalars().first()

    if not user or user.password_hash != req.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    tenant_res = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = tenant_res.scalars().first()

    if tenant and tenant.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant account is inactive or suspended."
        )

    token = create_jwt_token({
        "userId": user.id,
        "tenantId": user.tenant_id,
        "email": user.email,
        "role": user.role
    })

    return {
        "success": True,
        "data": {
            "token": token,
            "tenant": {"id": tenant.id if tenant else user.tenant_id, "name": tenant.name if tenant else "Default Tenant", "slug": tenant.slug if tenant else "tenant", "plan": tenant.plan if tenant else "STARTER"},
            "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role}
        }
    }
