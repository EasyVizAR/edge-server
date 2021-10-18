import os

from .main import app

if __name__ == "__main__":
    host = os.environ.get("VIZAR_HOST", "127.0.0.1")
    port = os.environ.get("VIZAR_PORT", 5000)
    app.run(host=host, port=port)
