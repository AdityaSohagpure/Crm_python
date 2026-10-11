import sys
from pathlib import Path

# Add root directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from a2wsgi import ASGIMiddleware
from main import app as asgi_app

# Native ASGI export for UvicornWorker
app = asgi_app

# WSGI wrapped export for synchronous Gunicorn workers
application = ASGIMiddleware(asgi_app)
