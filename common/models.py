import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey, Index, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from backend_python.common.database import Base

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
    status = Column(String, default="ACTIVE")
    plan = Column(String, default="STARTER")
    timezone = Column(String, default="UTC")
    max_agents = Column(Integer, default=10)
    max_monthly_messages = Column(Integer, default=25000)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    contacts = relationship("Contact", back_populates="tenant", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: f"user_{uuid.uuid4().hex[:10]}")
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="AGENT")
    avatar_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="users")

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(String, primary_key=True, default=lambda: f"cont_{uuid.uuid4().hex[:10]}")
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True, index=True)
    phone = Column(String, nullable=True, index=True)
    avatar_url = Column(String, nullable=True)
    channels = Column(JSON, default=[]) # Array of {channel, externalId, profileName}
    assigned_agent_id = Column(String, nullable=True)
    lead_status = Column(String, default="NEW")
    tags = Column(JSON, default=[])
    notes = Column(String, nullable=True)
    custom_fields = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="contacts")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=lambda: f"conv_{uuid.uuid4().hex[:10]}")
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_id = Column(String, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False, index=True)
    channel = Column(String, nullable=False) # 'whatsapp', 'facebook', 'instagram', 'email'
    channel_account_id = Column(String, nullable=True)
    external_thread_id = Column(String, nullable=False)
    status = Column(String, default="OPEN", index=True)
    assigned_agent_id = Column(String, nullable=True)
    unread_count = Column(Integer, default=0)
    last_message_text = Column(String, nullable=True)
    last_message_at = Column(DateTime, default=datetime.utcnow, index=True)
    tags = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: f"msg_{uuid.uuid4().hex[:10]}")
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_id = Column(String, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False)
    channel = Column(String, nullable=False)
    direction = Column(String, nullable=False) # 'INBOUND', 'OUTBOUND'
    sender_type = Column(String, nullable=False) # 'CUSTOMER', 'AGENT', 'BOT'
    sender_id = Column(String, nullable=True)
    external_message_id = Column(String, nullable=True, index=True)
    message_type = Column(String, default="text")
    content = Column(String, nullable=False)
    attachments = Column(JSON, default=[])
    status = Column(String, default="QUEUED")
    error_code = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(String, primary_key=True, default=lambda: f"evt_{uuid.uuid4().hex[:10]}")
    tenant_id = Column(String, nullable=True, index=True)
    provider = Column(String, nullable=False)
    event_id = Column(String, unique=True, nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    processed = Column(Boolean, default=False)
    error = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Deal(Base):
    __tablename__ = "deals"

    id = Column(String, primary_key=True, default=lambda: f"deal_{uuid.uuid4().hex[:10]}")
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    contact_person = Column(String, nullable=False)
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    value = Column(Integer, default=0)
    currency = Column(String, default="INR")
    stage = Column(String, default="New", index=True)
    score = Column(Integer, default=50)
    source = Column(String, default="Website")
    priority = Column(String, default="Medium")
    assigned_to = Column(String, default="Ananya Sharma")
    expected_close_date = Column(String, nullable=True)
    service_category = Column(String, default="Cloud Architecture & DevOps")
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
