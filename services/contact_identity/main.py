from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend_python.common.database import get_db_session, init_db
from backend_python.common.models import Contact, Conversation, Message
from backend_python.common.security import verify_jwt_token

app = FastAPI(
    title="Contact & Identity Microservice",
    description="Multi-Tenant Contacts, Conversations, and Message Retrieval Engine",
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

@app.get("/api/health")
async def health_check():
    return {
        "status": "ONLINE",
        "service": "Python Contact & Identity Microservice",
        "framework": "FastAPI + AsyncPG / SQLAlchemy"
    }

class CreateContactRequest(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    tags: Optional[List[str]] = []
    leadStatus: Optional[str] = "NEW"
    notes: Optional[str] = None

class CreateMessageRequest(BaseModel):
    messageType: Optional[str] = "text"
    content: str
    attachments: Optional[List[dict]] = []

@app.get("/api/v1/contacts")
async def get_contacts(user: dict = Depends(verify_jwt_token), db: AsyncSession = Depends(get_db_session)):
    tenant_id = user["tenantId"]
    result = await db.execute(select(Contact).where(Contact.tenant_id == tenant_id).order_by(Contact.updated_at.desc()))
    contacts = result.scalars().all()
    return {"success": True, "data": contacts}

@app.post("/api/v1/contacts", status_code=status.HTTP_201_CREATED)
async def create_contact(req: CreateContactRequest, user: dict = Depends(verify_jwt_token), db: AsyncSession = Depends(get_db_session)):
    tenant_id = user["tenantId"]
    contact = Contact(
        tenant_id=tenant_id,
        name=req.name,
        email=req.email,
        phone=req.phone,
        lead_status=req.leadStatus,
        tags=req.tags,
        notes=req.notes
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return {"success": True, "data": contact}

@app.get("/api/v1/conversations")
async def get_conversations(channel: Optional[str] = None, status: Optional[str] = None, user: dict = Depends(verify_jwt_token), db: AsyncSession = Depends(get_db_session)):
    tenant_id = user["tenantId"]
    query = select(Conversation).where(Conversation.tenant_id == tenant_id)
    if channel and channel != "all":
        query = query.where(Conversation.channel == channel)
    if status:
        query = query.where(Conversation.status == status)

    query = query.order_by(Conversation.last_message_at.desc())
    result = await db.execute(query)
    conversations = result.scalars().all()
    return {"success": True, "data": conversations}

@app.get("/api/v1/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str, user: dict = Depends(verify_jwt_token), db: AsyncSession = Depends(get_db_session)):
    tenant_id = user["tenantId"]
    result = await db.execute(
        select(Message).where(Message.tenant_id == tenant_id, Message.conversation_id == conversation_id).order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()
    return {"success": True, "data": messages}

@app.post("/api/v1/conversations/{conversation_id}/messages", status_code=status.HTTP_201_CREATED)
async def send_message(conversation_id: str, req: CreateMessageRequest, user: dict = Depends(verify_jwt_token), db: AsyncSession = Depends(get_db_session)):
    tenant_id = user["tenantId"]
    user_id = user["userId"]

    conv_res = await db.execute(select(Conversation).where(Conversation.tenant_id == tenant_id, Conversation.id == conversation_id))
    conversation = conv_res.scalars().first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation thread not found.")

    message = Message(
        tenant_id=tenant_id,
        conversation_id=conversation.id,
        contact_id=conversation.contact_id,
        channel=conversation.channel,
        direction="OUTBOUND",
        sender_type="AGENT",
        sender_id=user_id,
        message_type=req.messageType,
        content=req.content,
        attachments=req.attachments,
        status="SENT"
    )
    db.add(message)

    conversation.last_message_text = req.content
    await db.commit()
    await db.refresh(message)

    return {"success": True, "data": message}
