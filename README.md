# CRM Python Backend Services

Multi-Tenant Omnichannel CRM Backend Services built with FastAPI, SQLAlchemy (Async), PostgreSQL / SQLite, and Redis.

## Features
- **Gateway & Authentication Service**: Multi-tenant isolation, user registration, JWT authentication.
- **Channel Messaging Service**: Omnichannel messaging adapters (WhatsApp Cloud API, Facebook Messenger, Instagram Direct).
- **Contact & Identity Service**: Contacts, conversations, timeline, and customer messaging logs.
- **Webhook Receiver Service**: Sub-50ms Meta Graph API webhook ingestion engine.
- **Unified Cloud API**: Runs as a single unified service (`main.py`) or individual microservices (`run_services.py`).

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Unified API (Recommended)
```bash
uvicorn main:app --reload --port 8000
```
Interactive API documentation will be available at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 3. Run Microservices Cluster Individually
```bash
python run_services.py
```
- Gateway & Auth: `http://localhost:4000`
- Channel Messaging: `http://localhost:4001`
- Contact & Identity: `http://localhost:4002`
- Webhook Receiver: `http://localhost:4003`

### 4. Free Cloud Deployment (Render.com)
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables**:
  - `USE_SQLITE`: `true` (or provide `DATABASE_URL` for PostgreSQL)
  - `JWT_SECRET`: `your_random_secret_here`
