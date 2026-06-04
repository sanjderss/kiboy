import os
from app.server import start_xvfb, app
import uvicorn

if __name__ == "__main__":
    start_xvfb()
    uvicorn.run(app, host="0.0.0.0", port=8000)
