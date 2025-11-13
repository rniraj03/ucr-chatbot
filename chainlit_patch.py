from chainlit.server import app
from starlette.staticfiles import StaticFiles
import os

# Force re-mount the public directory for debugging
public_path = os.path.join(os.getcwd(), "public")
print("🔍 Manually mounting public dir:", public_path)

if os.path.exists(public_path):
    app.mount("/public", StaticFiles(directory=public_path), name="public")
    app.mount("/", StaticFiles(directory=public_path), name="root")
else:
    print("⚠️ No public directory found at:", public_path)
