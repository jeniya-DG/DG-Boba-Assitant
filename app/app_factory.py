# app/app_factory.py
from contextlib import asynccontextmanager
from fastapi import FastAPI

from .http_routes import http_router
from .ws_bridge import register_ws_routes
from .orders_store import init_store, clear_store

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: fresh orders.json
    init_store()
    print("🚀 Server starting, orders.json reset")
    try:
        yield
    finally:
        # Shutdown: wipe orders.json
        print("🔌 Server shutting down...")
        clear_store()

def create_app() -> FastAPI:
    app = FastAPI(title="Twilio ⇄ Deepgram Voice Agent (modular)", lifespan=lifespan)
    # HTTP routes (TwiML + Orders UI/JSON/SSE)
    app.include_router(http_router)
    # WebSocket route (/twilio)
    register_ws_routes(app)
    return app
