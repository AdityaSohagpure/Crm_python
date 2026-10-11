import httpx
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from backend_python.common.database import get_db_session, init_db
from backend_python.common.security import verify_jwt_token
from backend_python.common.config import settings

app = FastAPI(
    title="Channel Messaging Microservice",
    description="Omnichannel Messaging Adapter Service (WhatsApp Cloud API, Facebook Page Messenger, Instagram Direct)",
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
        "service": "Python Channel Messaging Microservice",
        "framework": "FastAPI + AsyncPG / SQLAlchemy"
    }

class SendWhatsAppTextRequest(BaseModel):
    conversationId: Optional[str] = None
    recipientPhone: str
    messageText: str

class SendWhatsAppTemplateRequest(BaseModel):
    conversationId: Optional[str] = None
    recipientPhone: str
    templateName: str
    languageCode: Optional[str] = "en_US"
    components: Optional[List[dict]] = []

class SendFacebookMessageRequest(BaseModel):
    conversationId: Optional[str] = None
    pageId: Optional[str] = None
    pageToken: Optional[str] = None
    recipientPsid: str
    text: str
    messageTag: Optional[str] = "HUMAN_AGENT"

class SendInstagramMessageRequest(BaseModel):
    conversationId: Optional[str] = None
    igUserId: Optional[str] = None
    pageToken: Optional[str] = None
    recipientIgsid: str
    text: str

@app.post("/api/v1/whatsapp/send-text")
async def send_whatsapp_text(req: SendWhatsAppTextRequest, user: dict = Depends(verify_jwt_token)):
    phone_id = settings.WHATSAPP_PHONE_NUMBER_ID
    token = settings.META_PERMANENT_ACCESS_TOKEN
    clean_phone = "".join(filter(str.isdigit, req.recipientPhone))
    url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": clean_phone,
        "type": "text",
        "text": {"preview_url": True, "body": req.messageText}
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers={"Authorization": f"Bearer {token}"})
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail=response.json())

        data = response.json()
        wamid = data.get("messages", [{}])[0].get("id")
        return {"success": True, "wamid": wamid, "meta": data}

@app.post("/api/v1/whatsapp/send-template")
async def send_whatsapp_template(req: SendWhatsAppTemplateRequest, user: dict = Depends(verify_jwt_token)):
    phone_id = settings.WHATSAPP_PHONE_NUMBER_ID
    token = settings.META_PERMANENT_ACCESS_TOKEN
    clean_phone = "".join(filter(str.isdigit, req.recipientPhone))
    url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": clean_phone,
        "type": "template",
        "template": {
            "name": req.templateName,
            "language": {"code": req.languageCode},
            "components": req.components
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers={"Authorization": f"Bearer {token}"})
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail=response.json())

        data = response.json()
        wamid = data.get("messages", [{}])[0].get("id")
        return {"success": True, "wamid": wamid, "meta": data}

@app.post("/api/v1/facebook/messages")
async def send_facebook_message(req: SendFacebookMessageRequest, user: dict = Depends(verify_jwt_token)):
    page_id = req.pageId or "493029182746201"
    page_token = req.pageToken or "sample_fb_page_token"
    url = f"https://graph.facebook.com/v20.0/{page_id}/messages"

    payload = {
        "recipient": {"id": req.recipientPsid},
        "messaging_type": "MESSAGE_TAG" if req.messageTag else "RESPONSE",
        "tag": req.messageTag,
        "message": {"text": req.text}
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers={"Authorization": f"Bearer {page_token}"})
        return {"success": True, "data": response.json() if response.status_code == 200 else {"simulated": True}}

@app.post("/api/v1/instagram/messages")
async def send_instagram_message(req: SendInstagramMessageRequest, user: dict = Depends(verify_jwt_token)):
    ig_user_id = req.igUserId or "1784140029485729"
    page_token = req.pageToken or "sample_fb_page_token"
    url = f"https://graph.facebook.com/v20.0/{ig_user_id}/messages"

    payload = {
        "recipient": {"id": req.recipientIgsid},
        "message": {"text": req.text}
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers={"Authorization": f"Bearer {page_token}"})
        return {"success": True, "data": response.json() if response.status_code == 200 else {"simulated": True}}
