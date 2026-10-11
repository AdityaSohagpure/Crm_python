import sys
from pathlib import Path

# Add root directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from a2wsgi import ASGIMiddleware
from main import app as asgi_app


class HybridApp:
    """Universal ASGI/WSGI callable adapter for Gunicorn and Uvicorn."""
    def __init__(self, app):
        self._asgi = app
        self._wsgi = ASGIMiddleware(app)

    def __call__(self, *args, **kwargs):
        # ASGI calling convention: (scope, receive, send)
        if len(args) == 3 and isinstance(args[0], dict) and "type" in args[0]:
            return self._asgi(*args, **kwargs)
        # WSGI calling convention: (environ, start_response)
        return self._wsgi(*args, **kwargs)


app = asgi_app
application = HybridApp(asgi_app)
