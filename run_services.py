import os
import sys
import types
from pathlib import Path
import multiprocessing
import uvicorn

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

def run_gateway_auth():
    uvicorn.run("backend_python.services.gateway_auth.main:app", host="0.0.0.0", port=4000, reload=False, log_level="info")

def run_channel_messaging():
    uvicorn.run("backend_python.services.channel_messaging.main:app", host="0.0.0.0", port=4001, reload=False, log_level="info")

def run_contact_identity():
    uvicorn.run("backend_python.services.contact_identity.main:app", host="0.0.0.0", port=4002, reload=False, log_level="info")

def run_webhook_receiver():
    uvicorn.run("backend_python.services.webhook_receiver.main:app", host="0.0.0.0", port=4003, reload=False, log_level="info")

if __name__ == "__main__":
    print("==================================================================")
    print("LAUNCHING PYTHON FASTAPI MULTI-TENANT MICROSERVICES CLUSTER")
    print("==================================================================")
    print("[Gateway & Auth Service]       --> http://localhost:4000")
    print("[Channel Messaging Service]    --> http://localhost:4001")
    print("[Contact & Identity Service]   --> http://localhost:4002")
    print("[Webhook Receiver Service]     --> http://localhost:4003")
    print("==================================================================")
    
    processes = [
        multiprocessing.Process(target=run_gateway_auth, name="GatewayAuthService"),
        multiprocessing.Process(target=run_channel_messaging, name="ChannelMessagingService"),
        multiprocessing.Process(target=run_contact_identity, name="ContactIdentityService"),
        multiprocessing.Process(target=run_webhook_receiver, name="WebhookReceiverService"),
    ]

    for p in processes:
        p.start()

    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        print("\nStopping Python Microservices...")
        for p in processes:
            p.terminate()
        sys.exit(0)
