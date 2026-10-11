import os

# Automatically bind to Render's dynamic PORT (e.g. 10000) on 0.0.0.0
port = os.getenv("PORT", "10000")
bind = f"0.0.0.0:{port}"
workers = 1
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
keepalive = 5
accesslog = "-"
errorlog = "-"
