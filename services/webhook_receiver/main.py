from fastapi import FastAPI, Request, Response, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend_python.common.database import get_db_session, init_db
from backend_python.common.models import WebhookEvent, Contact, Conversation, Message
from backend_python.common.config import settings

app = FastAPI(
    title="Meta & Email Webhook Receiver Microservice",
    description="Sub-50ms Meta Graph API Webhook Handshake and Asynchronous Event Ingestion Engine",
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
        "service": "Python Meta & Email Webhook Receiver Microservice",
        "framework": "FastAPI Sub-50ms Engine"
    }

@app.get("/api/v1/webhooks/meta")
async def verify_meta_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    expected_token = settings.META_WEBHOOK_VERIFY_TOKEN

    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        print("[Meta Webhook Verification] Handshake verified successfully!")
        return Response(content=hub_challenge, media_type="text/plain")

    print("[Meta Webhook Verification] Handshake failed!")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification token mismatch.")

@app.post("/api/v1/webhooks/meta")
async def receive_meta_webhook(request: Request, db: AsyncSession = Depends(get_db_session)):
    body = await request.json()

    if body.get("object") in ["whatsapp_business_account", "page"]:
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})

        tenant_id = "tenant_demo_123"

        # Inbound messages
        if "messages" in value:
            for msg in value.get("messages", []):
                from_phone = msg.get("from")
                wamid = msg.get("id")
                content = msg.get("text", {}).get("body", "[Media Payload]")

                # Idempotency check
                evt_res = await db.execute(select(WebhookEvent).where(WebhookEvent.event_id == wamid))
                if evt_res.scalars().first():
                    continue

                event = WebhookEvent(
                    tenant_id=tenant_id,
                    provider="meta",
                    event_id=wamid,
                    event_type="whatsapp_message_inbound",
                    payload=msg,
                    processed=True
                )
                db.add(event)
                await db.commit()
                print(f"[Python Microservice Inbound Webhook] Received from: {from_phone} | ID: {wamid}")

        return Response(content="EVENT_RECEIVED", status_code=200)

    raise HTTPException(status_code=404, detail="Unknown webhook payload object.")
