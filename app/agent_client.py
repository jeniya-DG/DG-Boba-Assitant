# agent_client.py
import json
import websockets
from websockets.legacy.client import WebSocketClientProtocol
from .settings import DG_API_KEY, build_deepgram_settings
from .agent_functions import FUNCTION_DEFS

async def connect_agent() -> WebSocketClientProtocol:
    return await websockets.connect(
        "wss://agent.deepgram.com/v1/agent/converse",
        subprotocols=["token", DG_API_KEY],
        max_size=2**24,
    )

async def send_agent_settings(ws: WebSocketClientProtocol):
    s = build_deepgram_settings()
    # inject tools under think.functions (Deepgram API requires this nesting)
    s["agent"]["think"]["functions"] = FUNCTION_DEFS
    await ws.send(json.dumps(s))
