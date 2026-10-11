import sys
from pathlib import Path

# Add root directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from a2wsgi import ASGIMiddleware
from main import app

# WSGI callable application for default Gunicorn invocation on Render
application = ASGIMiddleware(app)
app_wsgi = application
